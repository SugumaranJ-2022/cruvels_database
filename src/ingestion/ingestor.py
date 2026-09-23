"""
Document ingestion pipeline for extracting text from PDFs and performing deduplication.
"""

from datetime import datetime, timezone
import hashlib
import os
from typing import Optional

import pdfplumber
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.db.models import Document
from src.db.schemas import RawDocument
from src.ingestion.cleaner import clean_text
from src.ingestion.exceptions import (
    DuplicateDocumentError,
    EmptyDocumentError,
    UnsupportedFileTypeError,
)


def compute_content_hash(text: str) -> str:
    """
    Compute SHA256 hash of whitespace-normalized text for content deduplication.
    """
    normalized = " ".join(text.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def ingest_document(
    file_path: str,
    source: str,
    session: Optional[Session] = None,
    raw_id: Optional[str] = None,
) -> RawDocument:
    """
    Ingest a PDF document, extract per-page text, clean content, and check for duplicate hash.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found at path: {file_path}")

    if not file_path.lower().endswith(".pdf"):
        raise UnsupportedFileTypeError(
            f"Unsupported file format for '{file_path}'. Only PDF files are supported by pdfplumber."
        )

    page_texts: list[str] = []
    try:
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                extracted = page.extract_text()
                if extracted:
                    page_texts.append(extracted)
    except Exception as e:
        raise UnsupportedFileTypeError(f"Failed to parse PDF file '{file_path}': {str(e)}") from e

    if not page_texts or not "".join(page_texts).strip():
        raise EmptyDocumentError(f"No extractable text content found in document: {file_path}")

    raw_full_text = "\n\n".join(page_texts)
    content_hash = compute_content_hash(raw_full_text)

    # Database hash lookup for deduplication
    if session is not None:
        existing_doc = session.execute(
            select(Document).where(Document.content_hash == content_hash)
        ).scalar_one_or_none()
        if existing_doc:
            raise DuplicateDocumentError(
                message=f"duplicate_of: {existing_doc.id}",
                existing_document_id=str(existing_doc.id),
            )

    cleaned_text, cleaning_log = clean_text(raw_full_text, page_texts=page_texts)

    assigned_raw_id = raw_id if raw_id else os.path.basename(file_path)

    return RawDocument(
        raw_id=assigned_raw_id,
        source=source,
        doc_type_hint="unknown",
        clean_text=cleaned_text,
        cleaning_log=cleaning_log,
        content_hash=content_hash,
        ingested_at=datetime.now(timezone.utc),
        page_texts=page_texts,
    )
