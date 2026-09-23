"""
Knowledge Graph population module to upsert extracted entities and relationships.
"""

import logging
from typing import Dict, List
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Entity, Relationship, document_entities
from src.db.schemas import EntityCreate

logger = logging.getLogger(__name__)


async def upsert_entities(
    entities: List[EntityCreate],
    document_id: uuid.UUID,
    session: AsyncSession,
) -> Dict[str, Entity]:
    """
    Upsert entity records and associate them with the source document.
    Returns mapping of normalized_name -> Entity ORM object.
    """
    entity_map: Dict[str, Entity] = {}

    for ent in entities:
        stmt = select(Entity).where(
            Entity.type == ent.type,
            Entity.normalized_name == ent.normalized_name,
        )
        existing = (await session.execute(stmt)).scalar_one_or_none()

        if existing:
            entity_obj = existing
        else:
            entity_obj = Entity(
                type=ent.type,
                name=ent.name,
                normalized_name=ent.normalized_name,
            )
            session.add(entity_obj)
            await session.flush()

        entity_map[ent.normalized_name.lower()] = entity_obj

        # Link to document_entities
        link_stmt = select(document_entities).where(
            document_entities.c.document_id == document_id,
            document_entities.c.entity_id == entity_obj.id,
        )
        link_exists = (await session.execute(link_stmt)).first()
        if not link_exists:
            ins = document_entities.insert().values(
                document_id=document_id,
                entity_id=entity_obj.id,
            )
            await session.execute(ins)

    return entity_map


async def populate_knowledge_graph(
    relationships: List[Dict[str, str]],
    document_id: uuid.UUID,
    session: AsyncSession,
    entity_map: Dict[str, Entity],
) -> List[Relationship]:
    """
    Upsert provenance-tracked relationships into the knowledge graph.
    """
    rel_objects: List[Relationship] = []

    for r in relationships:
        from_name = r.get("from_entity", "").strip().lower()
        to_name = r.get("to_entity", "").strip().lower()
        relation_type = r.get("relation", "cites")

        if not from_name or not to_name:
            continue

        from_entity = entity_map.get(from_name)
        if not from_entity:
            logger.warning("Entity '%s' missing during relationship insertion; creating default entity.", from_name)
            from_entity = Entity(type="legal_concept", name=r["from_entity"], normalized_name=r["from_entity"])
            session.add(from_entity)
            await session.flush()
            entity_map[from_name] = from_entity

        to_entity = entity_map.get(to_name)
        if not to_entity:
            logger.warning("Entity '%s' missing during relationship insertion; creating default entity.", to_name)
            to_entity = Entity(type="legal_concept", name=r["to_entity"], normalized_name=r["to_entity"])
            session.add(to_entity)
            await session.flush()
            entity_map[to_name] = to_entity

        rel_obj = Relationship(
            from_entity_id=from_entity.id,
            relation=relation_type,
            to_entity_id=to_entity.id,
            source_document_id=document_id,
        )
        rel_objects.append(rel_obj)

    session.add_all(rel_objects)
    await session.flush()
    return rel_objects
