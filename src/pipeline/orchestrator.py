"""
End-to-end pipeline orchestrator for document ingestion, parsing, chunking, and graph storage.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Optional
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.chunking.chunker import build_chunks
from src.chunking.embedder import embed_and_store_chunks
from src.chunking.graph import populate_knowledge_graph, upsert_entities
from src.chunking.scoring import compute_authority_score, compute_recency_score
from src.db.models import Document
from src.db.schemas import ProcessingResult
from src.extraction.classifier import classify_document
from src.extraction.entities import extract_entities
from src.extraction.parsers import parse_act, parse_judgment, parse_regulation
from src.extraction.relationships import extract_relationships
from src.ingestion.cleaner import clean_text
from src.ingestion.exceptions import DuplicateDocumentError, EmptyDocumentError, UnsupportedFileTypeError
from src.ingestion.ingestor import compute_content_hash, ingest_document

logger = logging.getLogger(__name__)


async def process_document_end_to_end(
    file_path: str,
    source: str,
    session: AsyncSession,
    embedding_client: Optional[Any] = None,
) -> ProcessingResult:
    """
    Run Phases 2 to 4 end-to-end for a single document with stage-specific error handling.
    """
    cleaning_log = []
    current_stage = "Stage 1: Ingestion & Duplicate Check"

    try:
        # Stage 1: Ingestion & Duplicate Check
        raw_doc = ingest_document(file_path=file_path, source=source)
        cleaning_log = raw_doc.cleaning_log

        existing_doc = (
            await session.execute(
                select(Document).where(Document.content_hash == raw_doc.content_hash)
            )
        ).scalar_one_or_none()

        if existing_doc:
            return ProcessingResult(
                file_path=file_path,
                status="duplicate",
                document_id=existing_doc.id,
                duplicate_of=str(existing_doc.id),
                stage="Ingestion Check",
                cleaning_log=cleaning_log,
            )

        # Stage 2: Document Classification
        current_stage = "Stage 2: LLM Classification"
        classification = await classify_document(raw_doc.clean_text, session=session)
        doc_type = classification.doc_type

        # Stage 3: Structural Parsing
        current_stage = f"Stage 3: Structural Parsing ({doc_type})"
        structured_data: dict = {}
        parsed_date = None
        court_name = None
        case_number = None

        if doc_type == "judgment":
            judgment_obj = await parse_judgment(raw_doc.clean_text, page_texts=raw_doc.page_texts)
            structured_data = judgment_obj.model_dump()
            court_name = judgment_obj.court
            case_number = judgment_obj.case_number
            if judgment_obj.date:
                try:
                    parsed_date = datetime.strptime(judgment_obj.date, "%Y-%m-%d").date()
                except ValueError:
                    parsed_date = None
        elif doc_type == "act":
            act_obj = await parse_act(raw_doc.clean_text)
            structured_data = act_obj.model_dump()
        elif doc_type == "regulation":
            reg_obj = await parse_regulation(raw_doc.clean_text)
            structured_data = reg_obj.model_dump()
        else:
            structured_data = {"raw_text": raw_doc.clean_text[:2000]}

        # Calculate scores
        auth_score = compute_authority_score(court_name)
        rec_score = compute_recency_score(parsed_date)

        # Persist Document Record
        doc_record = Document(
            raw_id=raw_doc.raw_id,
            doc_type=doc_type,
            source=source,
            court=court_name,
            case_number=case_number,
            date=parsed_date,
            authority_score=auth_score,
            recency_score=rec_score,
            raw_text_ref=file_path,
            content_hash=raw_doc.content_hash,
        )
        session.add(doc_record)
        await session.flush()
        doc_id = doc_record.id

        # Stage 4: Entity & Relationship Extraction
        current_stage = "Stage 4: Entity & Relationship Extraction"
        extracted_ents = await extract_entities(structured_data, session=session)
        extracted_rels = await extract_relationships(structured_data, extracted_ents)

        # Stage 5: Knowledge Graph & Entity Upsert
        current_stage = "Stage 5: Knowledge Graph Storage"
        entity_map = await upsert_entities(extracted_ents, doc_id, session)
        await populate_knowledge_graph(extracted_rels, doc_id, session, entity_map)

        # Stage 6: Hierarchical Chunking & Embedding Storage
        current_stage = "Stage 6: Hierarchical Chunking & Embeddings"
        chunks = build_chunks(
            document_id=doc_id,
            doc_type=doc_type,
            structured_json=structured_data,
            authority_score=auth_score,
            recency_score=rec_score,
        )
        await embed_and_store_chunks(chunks, session, embedding_client=embedding_client)

        # Commit transaction
        await session.commit()

        return ProcessingResult(
            file_path=file_path,
            status="success",
            document_id=doc_id,
            stage="completed",
            cleaning_log=cleaning_log,
        )

    except UnsupportedFileTypeError as e:
        await session.rollback()
        logger.error("File error in %s at stage '%s': %s", file_path, current_stage, str(e))
        return ProcessingResult(
            file_path=file_path,
            status="failed",
            stage=current_stage,
            error_message=f"Unsupported file type: {str(e)}",
            cleaning_log=cleaning_log,
        )
    except EmptyDocumentError as e:
        await session.rollback()
        logger.error("Empty document error in %s at stage '%s': %s", file_path, current_stage, str(e))
        return ProcessingResult(
            file_path=file_path,
            status="failed",
            stage=current_stage,
            error_message=f"Empty document: {str(e)}",
            cleaning_log=cleaning_log,
        )
    except DuplicateDocumentError as e:
        await session.rollback()
        return ProcessingResult(
            file_path=file_path,
            status="duplicate",
            duplicate_of=e.existing_document_id,
            stage=current_stage,
            cleaning_log=cleaning_log,
        )
    except Exception as e:
        await session.rollback()
        logger.exception("Unexpected error in %s at stage '%s': %s", file_path, current_stage, str(e))
        return ProcessingResult(
            file_path=file_path,
            status="failed",
            stage=current_stage,
            error_message=f"Pipeline error at [{current_stage}]: {str(e)}",
            cleaning_log=cleaning_log,
        )
