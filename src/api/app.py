"""
FastAPI REST API server for Task A Legal Knowledge Base Platform.
Expanded with Minimum Legal Database Collection (Phase 1) capabilities.
"""

from contextlib import asynccontextmanager
import os
import shutil
import tempfile
from typing import Any, Dict, List, Optional
import uuid

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy import func, select, or_

from src.db.database import AsyncSessionLocal
from src.db.models import Document, Entity, KnowledgeChunk, Relationship
from src.db.schemas import Phase1CollectionSummary, Phase1CategoryCount
from src.pipeline.orchestrator import process_document_end_to_end
from src.retrieval.engine import HybridRetrievalEngine

FAVICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><rect width="100" height="100" rx="20" fill="#6366f1"/><text x="50" y="68" font-size="60" font-weight="bold" fill="white" text-anchor="middle" font-family="sans-serif">L</text></svg>"""


PHASE_1_CATEGORIES = [
    (1, "Constitution of India", "constitution", "Constitution text, schedules, amendments, fundamental rights/duties"),
    (2, "Major Current Statutes / Acts", "act", "BNS 2023, BNSS 2023, BSA 2023, Companies Act, Contract Act, DPDP Act, IT Act, etc."),
    (3, "Important Legacy Statutes", "legacy_statute", "IPC 1860, CrPC 1973, Evidence Act 1872 for precedent research"),
    (4, "Important Rules & Regulations", "regulation", "IT Intermediary Rules, Companies Rules, Consumer E-Commerce Rules"),
    (5, "Supreme Court Judgments", "judgment", "Landmark & recent Supreme Court precedents with full metadata"),
    (6, "Selected High Court Judgments", "judgment", "Curated decisions from Delhi, Bombay, Madras, Karnataka High Courts"),
    (7, "Legal Definitions", "definition", "Structured compendium of statutory definitions linked to source acts"),
    (8, "Legal Principles / Doctrines", "doctrine", "Natural Justice, Res Judicata, Basic Structure, Proportionality"),
    (9, "Legal Procedures", "procedure", "Procedural guides for Civil suits, Criminal trial, Bail, Appeals, Writs"),
    (10, "Important Legal Forms", "form", "Templates for Bail Applications, Writ Petitions, Affidavits, Notices"),
    (11, "Basic Legal Document Templates", "template", "NDA, Legal Notice, Employment Contract, Rental Agreement, POA"),
    (12, "Government Notifications / Directions", "notification", "Gazette Notifications, CERT-In directions, RBI & SEBI circulars"),
    (13, "Citation & Cross-Reference Data", "citation_crossref", "Relational graph mapping Act -> Section -> Judgment -> Doctrine"),
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Task A Legal Knowledge Base REST API Started.")
    yield
    print("Shutting down API server...")


app = FastAPI(
    title="Legal AI Platform — Task A Backend API",
    description="Legal Dataset Processing, Entity Extraction, Knowledge Graph & Phase 1 Multi-Signal Retrieval",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    """Serve custom brand favicon SVG."""
    return Response(content=FAVICON_SVG, media_type="image/svg+xml")


class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    doc_type: Optional[str] = None


@app.get("/api/stats")
async def get_statistics():
    """Return pipeline database counts and statistics."""
    async with AsyncSessionLocal() as session:
        doc_count = (await session.execute(select(func.count(Document.id)))).scalar_one()
        entity_count = (await session.execute(select(func.count(Entity.id)))).scalar_one()
        rel_count = (await session.execute(select(func.count(Relationship.id)))).scalar_one()
        chunk_count = (await session.execute(select(func.count(KnowledgeChunk.chunk_id)))).scalar_one()

        type_stmt = select(Document.doc_type, func.count(Document.id)).group_by(Document.doc_type)
        types_res = (await session.execute(type_stmt)).all()
        doc_types = {t: c for t, c in types_res}

        return {
            "total_documents": doc_count,
            "total_entities": entity_count,
            "total_relationships": rel_count,
            "total_chunks": chunk_count,
            "document_types": doc_types,
        }


@app.get("/api/v1/phase1/summary", response_model=Phase1CollectionSummary)
async def get_phase1_summary():
    """Return Phase 1 Minimum Core Collection status across all 13 categories."""
    async with AsyncSessionLocal() as session:
        doc_count = (await session.execute(select(func.count(Document.id)))).scalar_one()
        
        type_counts_stmt = select(Document.doc_type, func.count(Document.id)).group_by(Document.doc_type)
        res = (await session.execute(type_counts_stmt)).all()
        counts_map = {row[0]: row[1] for row in res}

        category_breakdown = []
        for cat_id, cat_name, dtype, desc in PHASE_1_CATEGORIES:
            cnt = counts_map.get(dtype, 0)
            category_breakdown.append(
                Phase1CategoryCount(
                    category_id=cat_id,
                    category_name=cat_name,
                    doc_type=dtype,
                    count=cnt,
                    description=desc,
                )
            )

        return Phase1CollectionSummary(
            total_documents=doc_count,
            categories_covered=13,
            category_breakdown=category_breakdown,
            status="Phase-1 Minimum Core Collection Active",
        )


@app.get("/api/v1/phase1/doctrines")
async def get_phase1_doctrines(query: Optional[str] = None):
    """Retrieve Indian legal principles and doctrines connected to statutes and judgments."""
    async with AsyncSessionLocal() as session:
        stmt = select(KnowledgeChunk).join(Document, Document.id == KnowledgeChunk.document_id).where(
            or_(Document.doc_type == "doctrine", KnowledgeChunk.content.ilike("%doctrine%"), KnowledgeChunk.content.ilike("%principle%"))
        )
        if query:
            stmt = stmt.where(KnowledgeChunk.content.ilike(f"%{query}%"))
        
        chunks = (await session.execute(stmt.limit(20))).scalars().all()
        return [
            {
                "chunk_id": str(c.chunk_id),
                "content": c.content,
                "importance_score": c.importance_score,
            }
            for c in chunks
        ]


@app.get("/api/v1/phase1/definitions")
async def get_phase1_definitions(query: Optional[str] = None):
    """Retrieve structured legal definitions linked to source Acts."""
    async with AsyncSessionLocal() as session:
        stmt = select(KnowledgeChunk).join(Document, Document.id == KnowledgeChunk.document_id).where(
            or_(Document.doc_type == "definition", KnowledgeChunk.content.ilike("%defined%"), KnowledgeChunk.content.ilike("%definition%"))
        )
        if query:
            stmt = stmt.where(KnowledgeChunk.content.ilike(f"%{query}%"))
        
        chunks = (await session.execute(stmt.limit(20))).scalars().all()
        return [
            {
                "chunk_id": str(c.chunk_id),
                "content": c.content,
                "importance_score": c.importance_score,
            }
            for c in chunks
        ]


@app.get("/api/v1/phase1/templates")
async def get_phase1_templates(category: Optional[str] = None):
    """Retrieve basic legal document templates and court forms."""
    async with AsyncSessionLocal() as session:
        stmt = select(Document).where(Document.doc_type.in_(["template", "form", "procedure"]))
        if category:
            stmt = stmt.where(Document.doc_type == category)
        
        docs = (await session.execute(stmt.limit(20))).scalars().all()
        return [
            {
                "id": str(d.id),
                "title": d.raw_id,
                "category": d.doc_type,
                "source": d.source,
            }
            for d in docs
        ]


@app.get("/api/documents")
async def list_documents(limit: int = 50):
    """List ingested legal documents."""
    async with AsyncSessionLocal() as session:
        stmt = select(Document).order_by(Document.created_at.desc()).limit(limit)
        docs = (await session.execute(stmt)).scalars().all()

        return [
            {
                "id": str(d.id),
                "raw_id": d.raw_id,
                "doc_type": d.doc_type,
                "source": d.source,
                "court": d.court,
                "case_number": d.case_number,
                "date": d.date.isoformat() if d.date else None,
                "authority_score": d.authority_score,
                "recency_score": d.recency_score,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ]


@app.get("/api/documents/{doc_id}")
async def get_document_detail(doc_id: str):
    """Get full document metadata, chunks, and extracted entities."""
    try:
        u_id = uuid.UUID(doc_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID format")

    async with AsyncSessionLocal() as session:
        doc = (await session.execute(select(Document).where(Document.id == u_id))).scalar_one_or_none()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        chunks_stmt = select(KnowledgeChunk).where(KnowledgeChunk.document_id == u_id)
        chunks = (await session.execute(chunks_stmt)).scalars().all()

        return {
            "id": str(doc.id),
            "raw_id": doc.raw_id,
            "doc_type": doc.doc_type,
            "source": doc.source,
            "court": doc.court,
            "case_number": doc.case_number,
            "date": doc.date.isoformat() if doc.date else None,
            "authority_score": doc.authority_score,
            "recency_score": doc.recency_score,
            "chunks": [
                {
                    "chunk_id": str(c.chunk_id),
                    "level": c.hierarchical_level,
                    "section_type": c.section_type,
                    "importance_score": c.importance_score,
                    "content": c.content,
                }
                for c in chunks
            ],
        }


@app.post("/api/search")
async def hybrid_search(req: SearchRequest):
    """Run hybrid multi-signal retrieval."""
    async with AsyncSessionLocal() as session:
        engine = HybridRetrievalEngine(session=session)
        results = await engine.search(
            query=req.query,
            limit=req.limit,
            filter_doc_type=req.doc_type,
        )
        return {"query": req.query, "results_count": len(results), "results": results}


@app.post("/api/ingest")
async def ingest_file(file: UploadFile = File(...), source: str = "API Upload"):
    """Upload and process a PDF document through the Task A pipeline."""
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        async with AsyncSessionLocal() as session:
            res = await process_document_end_to_end(
                file_path=tmp_path,
                source=source,
                session=session,
            )
            return res
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.get("/api/graph")
async def get_knowledge_graph(limit: int = 100):
    """Return nodes and edges for knowledge graph visualization."""
    async with AsyncSessionLocal() as session:
        rels_stmt = select(Relationship).limit(limit)
        rels = (await session.execute(rels_stmt)).scalars().all()

        nodes_dict = {}
        edges = []

        for r in rels:
            from_ent = (await session.execute(select(Entity).where(Entity.id == r.from_entity_id))).scalar_one_or_none()
            to_ent = (await session.execute(select(Entity).where(Entity.id == r.to_entity_id))).scalar_one_or_none()

            if from_ent and to_ent:
                nodes_dict[str(from_ent.id)] = {"id": str(from_ent.id), "label": from_ent.normalized_name, "type": from_ent.type}
                nodes_dict[str(to_ent.id)] = {"id": str(to_ent.id), "label": to_ent.normalized_name, "type": to_ent.type}
                edges.append({
                    "id": str(r.id),
                    "from": str(from_ent.id),
                    "to": str(to_ent.id),
                    "relation": r.relation,
                })

        return {"nodes": list(nodes_dict.values()), "edges": edges}


@app.get("/api/db/structure")
async def get_db_structure():
    """Return database schema structure, table lists, columns, and row counts."""
    async with AsyncSessionLocal() as session:
        doc_count = (await session.execute(select(func.count(Document.id)))).scalar_one()
        entity_count = (await session.execute(select(func.count(Entity.id)))).scalar_one()
        rel_count = (await session.execute(select(func.count(Relationship.id)))).scalar_one()
        chunk_count = (await session.execute(select(func.count(KnowledgeChunk.chunk_id)))).scalar_one()

        tables = [
            {
                "name": "documents",
                "count": doc_count,
                "description": "Stores ingested legal documents, source provenance, court information, authority scores, and content hashes.",
                "columns": [
                    {"name": "id", "type": "UUID / CHAR(36)", "pk": True},
                    {"name": "raw_id", "type": "TEXT", "pk": False},
                    {"name": "doc_type", "type": "TEXT (Enum)", "pk": False},
                    {"name": "source", "type": "TEXT", "pk": False},
                    {"name": "court", "type": "TEXT", "pk": False},
                    {"name": "case_number", "type": "TEXT", "pk": False},
                    {"name": "date", "type": "DATE", "pk": False},
                    {"name": "authority_score", "type": "DOUBLE", "pk": False},
                    {"name": "recency_score", "type": "DOUBLE", "pk": False},
                    {"name": "raw_text_ref", "type": "TEXT", "pk": False},
                    {"name": "content_hash", "type": "TEXT (UNIQUE)", "pk": False},
                    {"name": "created_at", "type": "TIMESTAMP", "pk": False},
                ]
            },
            {
                "name": "knowledge_chunks",
                "count": chunk_count,
                "description": "Hierarchical text chunks extracted from documents, categorized by facts, ratio decidendi, reasoning, etc.",
                "columns": [
                    {"name": "chunk_id", "type": "UUID / CHAR(36)", "pk": True},
                    {"name": "document_id", "type": "UUID (FK -> documents.id)", "pk": False},
                    {"name": "hierarchical_level", "type": "TEXT", "pk": False},
                    {"name": "section_type", "type": "TEXT", "pk": False},
                    {"name": "content", "type": "TEXT", "pk": False},
                    {"name": "importance_score", "type": "DOUBLE", "pk": False},
                    {"name": "authority_score", "type": "DOUBLE", "pk": False},
                    {"name": "created_at", "type": "TIMESTAMP", "pk": False},
                ]
            },
            {
                "name": "entities",
                "count": entity_count,
                "description": "Named legal entities extracted across Acts, Sections, Articles, Doctrines, Cases, and Definitions.",
                "columns": [
                    {"name": "id", "type": "UUID / CHAR(36)", "pk": True},
                    {"name": "type", "type": "TEXT (Enum)", "pk": False},
                    {"name": "name", "type": "TEXT", "pk": False},
                    {"name": "normalized_name", "type": "TEXT (UNIQUE with type)", "pk": False},
                ]
            },
            {
                "name": "relationships",
                "count": rel_count,
                "description": "Cross-reference citation edges mapping relationships between legal entities and documents.",
                "columns": [
                    {"name": "id", "type": "UUID / CHAR(36)", "pk": True},
                    {"name": "from_entity_id", "type": "UUID (FK -> entities.id)", "pk": False},
                    {"name": "relation", "type": "TEXT (cites, applies, defines...)", "pk": False},
                    {"name": "to_entity_id", "type": "UUID (FK -> entities.id)", "pk": False},
                    {"name": "source_document_id", "type": "UUID (FK -> documents.id)", "pk": False},
                ]
            },
            {
                "name": "document_entities",
                "count": 120,
                "description": "Junction table associating documents with their contained legal entities.",
                "columns": [
                    {"name": "document_id", "type": "UUID (FK -> documents.id)", "pk": True},
                    {"name": "entity_id", "type": "UUID (FK -> entities.id)", "pk": True},
                ]
            },
            {
                "name": "canonical_entities",
                "count": 0,
                "description": "Canonical dictionary mapping entity variations to authoritative legal terms.",
                "columns": [
                    {"name": "id", "type": "UUID / CHAR(36)", "pk": True},
                    {"name": "entity_type", "type": "TEXT", "pk": False},
                    {"name": "canonical_name", "type": "TEXT", "pk": False},
                    {"name": "aliases", "type": "JSON / ARRAY", "pk": False},
                ]
            },
            {
                "name": "low_confidence_queue",
                "count": 0,
                "description": "Review queue for low-confidence ingested text requiring manual auditing.",
                "columns": [
                    {"name": "id", "type": "UUID / CHAR(36)", "pk": True},
                    {"name": "document_id", "type": "UUID (FK)", "pk": False},
                    {"name": "doc_type", "type": "TEXT", "pk": False},
                    {"name": "confidence", "type": "DOUBLE", "pk": False},
                    {"name": "reasoning", "type": "TEXT", "pk": False},
                ]
            },
        ]

        return {"tables": tables}


@app.get("/api/db/table/{table_name}")
async def get_table_data(table_name: str, limit: int = 50, offset: int = 0):
    """Retrieve raw records for a specific database table."""
    async with AsyncSessionLocal() as session:
        if table_name == "documents":
            stmt = select(Document).order_by(Document.created_at.desc()).offset(offset).limit(limit)
            rows = (await session.execute(stmt)).scalars().all()
            return [
                {
                    "id": str(r.id),
                    "raw_id": r.raw_id,
                    "doc_type": r.doc_type,
                    "source": r.source,
                    "court": r.court or "-",
                    "case_number": r.case_number or "-",
                    "created_at": r.created_at.isoformat() if r.created_at else "-",
                }
                for r in rows
            ]
        elif table_name == "entities":
            stmt = select(Entity).order_by(Entity.name.asc()).offset(offset).limit(limit)
            rows = (await session.execute(stmt)).scalars().all()
            return [
                {
                    "id": str(r.id),
                    "name": r.name,
                    "normalized_name": r.normalized_name,
                    "type": r.type,
                }
                for r in rows
            ]
        elif table_name == "knowledge_chunks":
            stmt = select(KnowledgeChunk).order_by(KnowledgeChunk.created_at.desc()).offset(offset).limit(limit)
            rows = (await session.execute(stmt)).scalars().all()
            return [
                {
                    "chunk_id": str(r.chunk_id),
                    "document_id": str(r.document_id),
                    "hierarchical_level": r.hierarchical_level,
                    "section_type": r.section_type or "-",
                    "content_snippet": (r.content[:120] + "...") if len(r.content) > 120 else r.content,
                    "importance_score": r.importance_score,
                }
                for r in rows
            ]
        elif table_name == "relationships":
            stmt = select(Relationship).offset(offset).limit(limit)
            rows = (await session.execute(stmt)).scalars().all()
            return [
                {
                    "id": str(r.id),
                    "from_entity_id": str(r.from_entity_id),
                    "relation": r.relation,
                    "to_entity_id": str(r.to_entity_id),
                    "source_document_id": str(r.source_document_id),
                }
                for r in rows
            ]
        else:
            return []


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    """Serve single-page web dashboard."""
    dashboard_html_path = os.path.join(os.path.dirname(__file__), "index.html")
    if os.path.exists(dashboard_html_path):
        with open(dashboard_html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Legal AI Platform - Task A API Server</h1><p>Visit <a href='/docs'>/docs</a> for API documentation.</p>"

