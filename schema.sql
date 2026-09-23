-- Task A Legal Dataset Database Schema

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    raw_id TEXT NOT NULL,
    doc_type TEXT NOT NULL CHECK (doc_type IN ('judgment', 'act', 'constitution', 'legacy_statute', 'regulation', 'definition', 'doctrine', 'procedure', 'form', 'template', 'notification', 'citation_crossref', 'order', 'unknown')),
    source TEXT NOT NULL,
    court TEXT,
    case_number TEXT,
    act_name TEXT,
    date DATE,
    authority_score DOUBLE PRECISION,
    recency_score DOUBLE PRECISION,
    primary_topic TEXT,
    raw_text_ref TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_documents_content_hash ON documents(content_hash);

CREATE TABLE IF NOT EXISTS entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type TEXT NOT NULL CHECK (type IN ('act', 'section', 'constitution_article', 'schedule', 'amendment', 'case', 'court', 'judge', 'party', 'legal_concept', 'legal_doctrine', 'procedure', 'form_template', 'definition')),
    name TEXT NOT NULL,
    normalized_name TEXT NOT NULL,
    CONSTRAINT uq_entities_type_normalized UNIQUE (type, normalized_name)
);

CREATE TABLE IF NOT EXISTS document_entities (
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    PRIMARY KEY (document_id, entity_id)
);

CREATE TABLE IF NOT EXISTS relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    from_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation TEXT NOT NULL CHECK (relation IN ('cites', 'applies', 'interprets', 'overrules', 'belongs_to', 'defines', 'implements', 'amends', 'replaces', 'derives_from')),
    to_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    source_document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS knowledge_chunks (
    chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    hierarchical_level TEXT NOT NULL CHECK (hierarchical_level IN ('document', 'section', 'subsection', 'paragraph')),
    section_type TEXT CHECK (section_type IN ('facts', 'issues', 'reasoning', 'ratio_decidendi', 'decision', 'statute_section', 'other')),
    content TEXT NOT NULL,
    content_tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', content)) STORED,
    embedding VECTOR(1536),
    parent_chunk_id UUID REFERENCES knowledge_chunks(chunk_id) ON DELETE SET NULL,
    child_chunk_ids UUID[],
    importance_score DOUBLE PRECISION DEFAULT 1.0 NOT NULL,
    authority_score DOUBLE PRECISION,
    recency_score DOUBLE PRECISION,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS canonical_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,
    canonical_name TEXT NOT NULL,
    aliases TEXT[] NOT NULL DEFAULT '{}',
    CONSTRAINT uq_canonical_type_name UNIQUE (entity_type, canonical_name)
);

CREATE TABLE IF NOT EXISTS low_confidence_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    doc_type TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    reasoning TEXT NOT NULL,
    clean_text_snippet TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Foreign Key B-Tree Indexes
CREATE INDEX IF NOT EXISTS idx_doc_entities_document ON document_entities(document_id);
CREATE INDEX IF NOT EXISTS idx_doc_entities_entity ON document_entities(entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_from_entity ON relationships(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_to_entity ON relationships(to_entity_id);
CREATE INDEX IF NOT EXISTS idx_relationships_source_doc ON relationships(source_document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON knowledge_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_parent_chunk_id ON knowledge_chunks(parent_chunk_id);

-- Full-Text Search GIN Index
CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv ON knowledge_chunks USING GIN(content_tsv);

-- Vector Embedding HNSW Index
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw ON knowledge_chunks USING hnsw (embedding vector_cosine_ops);
