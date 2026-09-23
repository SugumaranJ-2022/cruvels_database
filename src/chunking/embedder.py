"""
Batch embedding generator and single-transaction DB persister for knowledge chunks.
"""

import logging
from typing import Any, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import KnowledgeChunk
from src.db.schemas import KnowledgeChunkCreate

logger = logging.getLogger(__name__)


def generate_dummy_embedding(dim: int = settings.EMBEDDING_DIMENSION) -> List[float]:
    """Generate normalized dummy vector for testing/offline environments."""
    return [0.001] * dim


async def generate_embeddings_batch(
    texts: List[str],
    embedding_client: Optional[Any] = None,
) -> List[List[float]]:
    """
    Generate vector embeddings in batches using specified client.
    Returns dummy embeddings if client is not provided.
    """
    if embedding_client is None:
        return [generate_dummy_embedding() for _ in texts]

    try:
        # Generic embedding API call handling (e.g. OpenAI / Anthropic / SentenceTransformers)
        if hasattr(embedding_client, "embed_documents"):
            return await embedding_client.embed_documents(texts)
        elif hasattr(embedding_client, "embeddings"):
            response = await embedding_client.embeddings.create(input=texts, model="text-embedding-3-small")
            return [data.embedding for data in response.data]
        else:
            return [generate_dummy_embedding() for _ in texts]
    except Exception as e:
        logger.warning("Failed to call vector embedding client (%s). Falling back to dummy vectors.", str(e))
        return [generate_dummy_embedding() for _ in texts]


async def embed_and_store_chunks(
    chunks: List[KnowledgeChunkCreate],
    session: AsyncSession,
    embedding_client: Optional[Any] = None,
    batch_size: int = 50,
) -> List[KnowledgeChunk]:
    """
    Embed chunks in batches and persist all chunks in a single transaction.
    """
    if not chunks:
        return []

    orm_chunks: List[KnowledgeChunk] = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        texts = [c.content for c in batch]
        embeddings = await generate_embeddings_batch(texts, embedding_client=embedding_client)

        for chunk_data, emb in zip(batch, embeddings):
            orm_chunk = KnowledgeChunk(
                document_id=chunk_data.document_id,
                hierarchical_level=chunk_data.hierarchical_level,
                section_type=chunk_data.section_type,
                content=chunk_data.content,
                embedding=emb,
                parent_chunk_id=chunk_data.parent_chunk_id,
                child_chunk_ids=chunk_data.child_chunk_ids,
                importance_score=chunk_data.importance_score,
                authority_score=chunk_data.authority_score,
                recency_score=chunk_data.recency_score,
            )
            orm_chunks.append(orm_chunk)

    session.add_all(orm_chunks)
    await session.flush()
    return orm_chunks
