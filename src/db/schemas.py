"""
Pydantic data models and schemas for API, ingestion, LLM parsing, and database insertion.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Literal, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

DocTypeLiteral = Literal[
    "judgment",
    "act",
    "constitution",
    "legacy_statute",
    "regulation",
    "definition",
    "doctrine",
    "procedure",
    "form",
    "template",
    "notification",
    "citation_crossref",
    "order",
    "unknown",
]

EntityTypeLiteral = Literal[
    "act",
    "section",
    "constitution_article",
    "schedule",
    "amendment",
    "case",
    "court",
    "judge",
    "party",
    "legal_concept",
    "legal_doctrine",
    "procedure",
    "form_template",
    "definition",
]

RelationTypeLiteral = Literal[
    "cites",
    "applies",
    "interprets",
    "overrules",
    "belongs_to",
    "defines",
    "implements",
    "amends",
    "replaces",
    "derives_from",
]


class DocumentCreate(BaseModel):
    """Pydantic model for creating a document record."""
    raw_id: str
    doc_type: DocTypeLiteral
    source: str
    court: Optional[str] = None
    case_number: Optional[str] = None
    act_name: Optional[str] = None
    date: Optional[date] = None
    authority_score: Optional[float] = None
    recency_score: Optional[float] = None
    primary_topic: Optional[str] = None
    raw_text_ref: str
    content_hash: str


class DocumentRead(DocumentCreate):
    """Pydantic model for reading a document record."""
    id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntityCreate(BaseModel):
    """Pydantic model for creating an entity record."""
    type: EntityTypeLiteral
    name: str
    normalized_name: str


class EntityRead(EntityCreate):
    """Pydantic model for reading an entity record."""
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class DocumentEntityCreate(BaseModel):
    """Pydantic model for linking a document to an entity."""
    document_id: uuid.UUID
    entity_id: uuid.UUID


class RelationshipCreate(BaseModel):
    """Pydantic model for creating a relationship record."""
    from_entity_id: uuid.UUID
    relation: RelationTypeLiteral
    to_entity_id: uuid.UUID
    source_document_id: uuid.UUID


class RelationshipRead(RelationshipCreate):
    """Pydantic model for reading a relationship record."""
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class KnowledgeChunkCreate(BaseModel):
    """Pydantic model for creating a knowledge chunk record."""
    document_id: uuid.UUID
    hierarchical_level: Literal["document", "section", "subsection", "paragraph"]
    section_type: Optional[Literal["facts", "issues", "reasoning", "ratio_decidendi", "decision", "statute_section", "other"]] = None
    content: str
    embedding: Optional[List[float]] = None
    parent_chunk_id: Optional[uuid.UUID] = None
    child_chunk_ids: Optional[List[uuid.UUID]] = None
    importance_score: float = 1.0
    authority_score: Optional[float] = None
    recency_score: Optional[float] = None


class KnowledgeChunkRead(KnowledgeChunkCreate):
    """Pydantic model for reading a knowledge chunk record."""
    chunk_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CanonicalEntityCreate(BaseModel):
    """Pydantic model for creating a canonical entity lookup entry."""
    entity_type: str
    canonical_name: str
    aliases: List[str] = Field(default_factory=list)


class CanonicalEntityRead(CanonicalEntityCreate):
    """Pydantic model for reading a canonical entity lookup entry."""
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


class LowConfidenceQueueCreate(BaseModel):
    """Pydantic model for creating a low-confidence classification log."""
    document_id: Optional[uuid.UUID] = None
    doc_type: str
    confidence: float
    reasoning: str
    clean_text_snippet: str


class RawDocument(BaseModel):
    """Pydantic model representing an ingested raw document before LLM parsing."""
    raw_id: str
    source: str
    doc_type_hint: DocTypeLiteral = "unknown"
    clean_text: str
    cleaning_log: List[str]
    content_hash: str
    ingested_at: datetime
    page_texts: List[str]


class DocClassification(BaseModel):
    """Pydantic schema for document classification LLM output."""
    doc_type: DocTypeLiteral = "judgment"
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    reasoning: str = "Classified based on document legal structure"


class PartiesSchema(BaseModel):
    """Pydantic schema for party details in judgments."""
    petitioner: List[str] = Field(default_factory=list)
    respondent: List[str] = Field(default_factory=list)


class ArgumentsSchema(BaseModel):
    """Pydantic schema for party arguments in judgments."""
    petitioner: str = ""
    respondent: str = ""


class JudgmentSchema(BaseModel):
    """Pydantic schema for structured judgment LLM extraction."""
    court: Optional[str] = None
    case_number: Optional[str] = None
    date: Optional[str] = None
    judges: List[str] = Field(default_factory=list)
    parties: PartiesSchema = Field(default_factory=PartiesSchema)
    statutes_cited: List[str] = Field(default_factory=list)
    facts: str = ""
    issues: List[str] = Field(default_factory=list)
    arguments: ArgumentsSchema = Field(default_factory=ArgumentsSchema)
    reasoning: str = ""
    decision: str = ""
    ratio_decidendi: str = ""
    obiter_dicta: Optional[str] = None
    citations: List[str] = Field(default_factory=list)


class SubsectionSchema(BaseModel):
    """Pydantic schema for Act subsection parsing."""
    sub_number: str
    text: str


class SectionSchema(BaseModel):
    """Pydantic schema for Act section parsing."""
    section_number: str
    section_title: Optional[str] = None
    text: str
    subsections: List[SubsectionSchema] = Field(default_factory=list)


class ChapterSchema(BaseModel):
    """Pydantic schema for Act chapter parsing."""
    chapter_number: str
    chapter_title: str
    sections: List[SectionSchema] = Field(default_factory=list)


class ActSchema(BaseModel):
    """Pydantic schema for structured Act LLM extraction."""
    act_name: str
    act_number: Optional[str] = None
    year: Optional[int] = None
    chapters: List[ChapterSchema] = Field(default_factory=list)


class RegulationSchema(BaseModel):
    """Pydantic schema for structured Regulation LLM extraction."""
    title: str
    issuing_authority: str
    date: Optional[str] = None
    reference_number: Optional[str] = None
    subject: str
    operative_text: str
    referenced_acts: List[str] = Field(default_factory=list)


class ExtractedEntityItem(BaseModel):
    """Individual entity extracted by LLM."""
    type: EntityTypeLiteral
    name: str
    normalized_name: str


class ExtractedEntitiesContainer(BaseModel):
    """Container schema for extracted entities list."""
    entities: List[ExtractedEntityItem] = Field(default_factory=list)


class ExtractedRelationshipItem(BaseModel):
    """Individual relationship extracted by LLM."""
    from_entity: str = Field(alias="from")
    relation: RelationTypeLiteral
    to_entity: str = Field(alias="to")

    model_config = ConfigDict(populate_by_name=True)


class ExtractedRelationshipsContainer(BaseModel):
    """Container schema for extracted relationships list."""
    relationships: List[ExtractedRelationshipItem] = Field(default_factory=list)


class ProcessingResult(BaseModel):
    """Summary of processing status for an ingested document."""
    file_path: str
    status: Literal["success", "failed", "duplicate"]
    document_id: Optional[uuid.UUID] = None
    duplicate_of: Optional[str] = None
    stage: str = "completed"
    error_message: Optional[str] = None
    cleaning_log: List[str] = Field(default_factory=list)


class Phase1CategoryCount(BaseModel):
    category_id: int
    category_name: str
    doc_type: str
    count: int
    description: str


class Phase1CollectionSummary(BaseModel):
    total_documents: int
    categories_covered: int
    category_breakdown: List[Phase1CategoryCount]
    status: str = "Phase-1 Minimum Core Collection Active"
