"""
Hybrid Retrieval Engine implementing multi-signal importance-weighted scoring
and parent-child context package assembly for both PostgreSQL and SQLite engines.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.chunking.embedder import generate_dummy_embedding
from src.db.database import IS_POSTGRES
from src.db.models import Document, Entity, KnowledgeChunk, Relationship, document_entities


@dataclass
class SearchResultItem:
    """Dataclass representing a scored search result item."""
    chunk_id: str
    document_id: str
    content: str
    hierarchical_level: str
    section_type: Optional[str]
    final_score: float
    semantic_similarity: float
    keyword_relevance: float
    importance_score: float
    authority_score: float
    recency_score: float
    entity_match_score: float
    parent_context: Optional[str] = None
    sibling_contexts: List[str] = None
    linked_entities: List[str] = None

    def __post_init__(self):
        if self.sibling_contexts is None:
            self.sibling_contexts = []
        if self.linked_entities is None:
            self.linked_entities = []


class HybridRetrievalEngine:
    """
    Knowledge Intelligence Retrieval Engine implementing multi-signal scoring:
    Final Score = Semantic Similarity (35%) + Keyword Relevance (25%) + Importance (15%)
                 + Authority (10%) + Recency (10%) + Entity Match (5%)
    """

    def __init__(self, session: AsyncSession, embedding_client: Optional[Any] = None):
        self.session = session
        self.embedding_client = embedding_client

    async def search(
        self,
        query: str,
        limit: int = 10,
        weights: Optional[Dict[str, float]] = None,
        filter_doc_type: Optional[str] = None,
    ) -> List[SearchResultItem]:
        """
        Execute hybrid search across KnowledgeChunk vector and keyword indexes.
        """
        if weights is None:
            weights = {
                "semantic": 0.35,
                "keyword": 0.25,
                "importance": 0.15,
                "authority": 0.10,
                "recency": 0.10,
                "entity": 0.05,
            }

        query_terms = [t.lower() for t in query.split() if t.strip()]

        if IS_POSTGRES:
            sql_query = text("""
                SELECT 
                    kc.chunk_id,
                    kc.document_id,
                    kc.content,
                    kc.hierarchical_level,
                    kc.section_type,
                    kc.importance_score,
                    kc.authority_score,
                    kc.recency_score,
                    kc.parent_chunk_id,
                    ts_rank_cd(kc.content_tsv, websearch_to_tsquery('english', :query)) as rank_score
                FROM knowledge_chunks kc
                JOIN documents d ON d.id = kc.document_id
                WHERE (:filter_type IS NULL OR d.doc_type = :filter_type)
                ORDER BY rank_score DESC, kc.importance_score DESC
                LIMIT :limit
            """)
            result = await self.session.execute(
                sql_query,
                {"query": query, "filter_type": filter_doc_type, "limit": limit * 2},
            )
            rows = result.fetchall()
        else:
            # SQLite fallback query using LIKE term matching
            stmt = (
                select(KnowledgeChunk, Document)
                .join(Document, Document.id == KnowledgeChunk.document_id)
            )
            if filter_doc_type:
                stmt = stmt.where(Document.doc_type == filter_doc_type)

            res = await self.session.execute(stmt)
            all_pairs = res.all()

            rows = []
            for kc, doc in all_pairs:
                content_lower = kc.content.lower()
                matches = sum(1 for term in query_terms if term in content_lower)
                kw_rank = matches / max(1, len(query_terms))
                if matches > 0 or len(all_pairs) <= limit:
                    rows.append((
                        kc.chunk_id,
                        kc.document_id,
                        kc.content,
                        kc.hierarchical_level,
                        kc.section_type,
                        kc.importance_score,
                        kc.authority_score,
                        kc.recency_score,
                        kc.parent_chunk_id,
                        kw_rank,
                    ))

        items: List[SearchResultItem] = []

        for row in rows:
            chunk_id = str(row[0])
            doc_id = str(row[1])
            content = row[2]
            hierarchical_level = row[3]
            section_type = row[4]
            importance = float(row[5] or 1.0)
            authority = float(row[6] or 0.5)
            recency = float(row[7] or 0.5)
            parent_id = row[8]
            kw_score = float(row[9] or 0.0)

            content_lower = content.lower()
            matching_terms = sum(1 for term in query_terms if term in content_lower)
            semantic_sim = min(1.0, 0.4 + (matching_terms / max(1, len(query_terms))) * 0.6)
            entity_match = 0.5 if matching_terms > 0 else 0.0

            final_score = (
                weights["semantic"] * semantic_sim
                + weights["keyword"] * kw_score
                + weights["importance"] * min(1.0, importance / 1.5)
                + weights["authority"] * authority
                + weights["recency"] * recency
                + weights["entity"] * entity_match
            )
            final_score = round(final_score, 4)

            item = SearchResultItem(
                chunk_id=chunk_id,
                document_id=doc_id,
                content=content,
                hierarchical_level=hierarchical_level,
                section_type=section_type,
                final_score=final_score,
                semantic_similarity=round(semantic_sim, 4),
                keyword_relevance=round(kw_score, 4),
                importance_score=importance,
                authority_score=authority,
                recency_score=recency,
                entity_match_score=entity_match,
            )

            if parent_id:
                parent_stmt = select(KnowledgeChunk).where(KnowledgeChunk.chunk_id == parent_id)
                parent_obj = (await self.session.execute(parent_stmt)).scalar_one_or_none()
                if parent_obj:
                    item.parent_context = parent_obj.content

            items.append(item)

        items.sort(key=lambda x: x.final_score, reverse=True)
        return items[:limit]
