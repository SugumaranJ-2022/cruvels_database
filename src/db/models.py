"""
SQLAlchemy 2.0 ORM models compatible with both PostgreSQL and SQLite fallback engines.
"""

from datetime import date, datetime
import json
from typing import Any, List, Optional
import uuid

from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    JSON,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from src.db.database import IS_POSTGRES

if IS_POSTGRES:
    from pgvector.sqlalchemy import Vector
    from sqlalchemy.dialects.postgresql import TSVECTOR, UUID as PG_UUID
    UUID_TYPE = PG_UUID(as_uuid=True)
    VECTOR_TYPE = Vector(1536)
    TSVECTOR_TYPE = TSVECTOR
    ARRAY_TYPE = ARRAY(Text)
    UUID_ARRAY_TYPE = ARRAY(PG_UUID(as_uuid=True))
    DEFAULT_UUID = text("gen_random_uuid()")
else:
    from sqlalchemy.types import TypeDecorator, CHAR, TEXT

    class GUID(TypeDecorator):
        """Platform-independent GUID type for SQLite."""
        impl = CHAR
        cache_ok = True

        def load_dialect_impl(self, dialect):
            return dialect.type_descriptor(CHAR(36))

        def process_bind_param(self, value, dialect):
            if value is None:
                return value
            elif isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(uuid.UUID(value))

        def process_result_value(self, value, dialect):
            if value is None:
                return value
            else:
                if not isinstance(value, uuid.UUID):
                    return uuid.UUID(value)
                return value

    UUID_TYPE = GUID()
    VECTOR_TYPE = JSON()
    TSVECTOR_TYPE = Text()
    ARRAY_TYPE = JSON()
    UUID_ARRAY_TYPE = JSON()
    DEFAULT_UUID = None


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# Composite primary key association table for document_entities
document_entities = Table(
    "document_entities",
    Base.metadata,
    Column("document_id", UUID_TYPE, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True),
    Column("entity_id", UUID_TYPE, ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True),
    Index("idx_doc_entities_document", "document_id"),
    Index("idx_doc_entities_entity", "entity_id"),
)


class Document(Base):
    """ORM Model representing a raw legal document entry."""
    __tablename__ = "documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, primary_key=True, default=uuid.uuid4, server_default=DEFAULT_UUID
    )
    raw_id: Mapped[str] = mapped_column(Text, nullable=False)
    doc_type: Mapped[str] = mapped_column(
        Text,
        CheckConstraint("doc_type IN ('judgment', 'act', 'constitution', 'legacy_statute', 'regulation', 'definition', 'doctrine', 'procedure', 'form', 'template', 'notification', 'citation_crossref', 'order', 'unknown')"),
        nullable=False,
    )
    source: Mapped[str] = mapped_column(Text, nullable=False)
    court: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    case_number: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    act_name: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    authority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    primary_topic: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_text_ref: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    entities: Mapped[List["Entity"]] = relationship(
        "Entity", secondary=document_entities, back_populates="documents"
    )
    knowledge_chunks: Mapped[List["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk", back_populates="document", cascade="all, delete-orphan"
    )
    source_relationships: Mapped[List["Relationship"]] = relationship(
        "Relationship", back_populates="source_document", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_documents_content_hash", "content_hash", unique=True),
    )


class Entity(Base):
    """ORM Model representing an extracted named legal entity."""
    __tablename__ = "entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, primary_key=True, default=uuid.uuid4, server_default=DEFAULT_UUID
    )
    type: Mapped[str] = mapped_column(
        Text,
        CheckConstraint("type IN ('act', 'section', 'constitution_article', 'schedule', 'amendment', 'case', 'court', 'judge', 'party', 'legal_concept', 'legal_doctrine', 'procedure', 'form_template', 'definition')"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(Text, nullable=False)

    documents: Mapped[List["Document"]] = relationship(
        "Document", secondary=document_entities, back_populates="entities"
    )
    outgoing_relationships: Mapped[List["Relationship"]] = relationship(
        "Relationship", foreign_keys="[Relationship.from_entity_id]", back_populates="from_entity"
    )
    incoming_relationships: Mapped[List["Relationship"]] = relationship(
        "Relationship", foreign_keys="[Relationship.to_entity_id]", back_populates="to_entity"
    )

    __table_args__ = (
        UniqueConstraint("type", "normalized_name", name="uq_entities_type_normalized"),
    )


class Relationship(Base):
    """ORM Model representing a typed provenance-tracked relationship between entities."""
    __tablename__ = "relationships"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, primary_key=True, default=uuid.uuid4, server_default=DEFAULT_UUID
    )
    from_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    relation: Mapped[str] = mapped_column(
        Text,
        CheckConstraint("relation IN ('cites', 'applies', 'interprets', 'overrules', 'belongs_to', 'defines', 'implements', 'amends', 'replaces', 'derives_from')"),
        nullable=False,
    )
    to_entity_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False
    )
    source_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )

    from_entity: Mapped["Entity"] = relationship(
        "Entity", foreign_keys=[from_entity_id], back_populates="outgoing_relationships"
    )
    to_entity: Mapped["Entity"] = relationship(
        "Entity", foreign_keys=[to_entity_id], back_populates="incoming_relationships"
    )
    source_document: Mapped["Document"] = relationship(
        "Document", back_populates="source_relationships"
    )

    __table_args__ = (
        Index("idx_relationships_from_entity", "from_entity_id"),
        Index("idx_relationships_to_entity", "to_entity_id"),
        Index("idx_relationships_source_doc", "source_document_id"),
    )


class KnowledgeChunk(Base):
    """ORM Model representing a hierarchical text chunk with vector and text indices."""
    __tablename__ = "knowledge_chunks"

    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, primary_key=True, default=uuid.uuid4, server_default=DEFAULT_UUID
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    hierarchical_level: Mapped[str] = mapped_column(
        Text,
        CheckConstraint("hierarchical_level IN ('document', 'section', 'subsection', 'paragraph')"),
        nullable=False,
    )
    section_type: Mapped[Optional[str]] = mapped_column(
        Text,
        CheckConstraint(
            "section_type IS NULL OR section_type IN ('facts', 'issues', 'reasoning', 'ratio_decidendi', 'decision', 'statute_section', 'other')"
        ),
        nullable=True,
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_tsv: Mapped[Optional[Any]] = mapped_column(TSVECTOR_TYPE, nullable=True)
    embedding: Mapped[Optional[Any]] = mapped_column(VECTOR_TYPE, nullable=True)
    parent_chunk_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID_TYPE, ForeignKey("knowledge_chunks.chunk_id", ondelete="SET NULL"), nullable=True
    )
    child_chunk_ids: Mapped[Optional[Any]] = mapped_column(UUID_ARRAY_TYPE, nullable=True)
    importance_score: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("1.0"))
    authority_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    document: Mapped["Document"] = relationship("Document", back_populates="knowledge_chunks")
    parent_chunk: Mapped[Optional["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk", remote_side=[chunk_id], back_populates="child_chunks"
    )
    child_chunks: Mapped[List["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk", back_populates="parent_chunk"
    )

    __table_args__ = (
        Index("idx_chunks_document_id", "document_id"),
        Index("idx_chunks_parent_chunk_id", "parent_chunk_id"),
    )


class CanonicalEntity(Base):
    """ORM Model for canonical entity normalization lookup table."""
    __tablename__ = "canonical_entities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, primary_key=True, default=uuid.uuid4, server_default=DEFAULT_UUID
    )
    entity_type: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_name: Mapped[str] = mapped_column(Text, nullable=False)
    aliases: Mapped[Any] = mapped_column(ARRAY_TYPE, nullable=False, default=list)

    __table_args__ = (
        UniqueConstraint("entity_type", "canonical_name", name="uq_canonical_type_name"),
    )


class LowConfidenceQueue(Base):
    """ORM Model for logging document classifications requiring manual review."""
    __tablename__ = "low_confidence_queue"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID_TYPE, primary_key=True, default=uuid.uuid4, server_default=DEFAULT_UUID
    )
    document_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID_TYPE, ForeignKey("documents.id", ondelete="CASCADE"), nullable=True
    )
    doc_type: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    clean_text_snippet: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
