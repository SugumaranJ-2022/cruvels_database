"""
Relationship extraction module connecting extracted entities with provenance.
Includes fallback text relationship parser.
"""

import json
from typing import Dict, List
from src.db.schemas import EntityCreate, ExtractedRelationshipsContainer
from src.extraction.llm_client import call_llm_with_validation, get_anthropic_client

RELATIONSHIP_SYSTEM_PROMPT = """
Given the structured document data and its extracted entities, identify relationships
between them. Only extract relationships explicitly supported by the text.

Relation types: "cites", "applies", "interprets", "overrules", "belongs_to", "defines", "implements", "amends", "replaces", "derives_from"

Respond with ONLY JSON: {"relationships": [{"from": "...", "relation": "...", "to": "..."}]}
"""


def _extract_relationships_fallback(entities: List[EntityCreate]) -> List[Dict[str, str]]:
    """Heuristic relationship extractor based on entity pairs."""
    rels: List[Dict[str, str]] = []

    case_entities = [e for e in entities if e.type == "case"]
    act_entities = [e for e in entities if e.type in ("act", "constitution_article", "amendment")]
    section_entities = [e for e in entities if e.type in ("section", "constitution_article")]
    court_entities = [e for e in entities if e.type == "court"]
    doctrine_entities = [e for e in entities if e.type == "legal_doctrine"]
    def_entities = [e for e in entities if e.type == "definition"]

    # Case applies Act / Section / Doctrine
    for c in case_entities:
        for a in act_entities:
            rels.append({"from_entity": c.normalized_name, "relation": "applies", "to_entity": a.normalized_name})
        for s in section_entities:
            rels.append({"from_entity": c.normalized_name, "relation": "cites", "to_entity": s.normalized_name})
        for court in court_entities:
            rels.append({"from_entity": c.normalized_name, "relation": "belongs_to", "to_entity": court.normalized_name})
        for doct in doctrine_entities:
            rels.append({"from_entity": c.normalized_name, "relation": "interprets", "to_entity": doct.normalized_name})

    # Section belongs to Act
    for s in section_entities:
        for a in act_entities:
            rels.append({"from_entity": s.normalized_name, "relation": "belongs_to", "to_entity": a.normalized_name})

    # Definition defines Section/Act
    for d in def_entities:
        for a in act_entities:
            rels.append({"from_entity": d.normalized_name, "relation": "defines", "to_entity": a.normalized_name})

    if not rels and len(entities) >= 2:
        rels.append({"from_entity": entities[0].normalized_name, "relation": "applies", "to_entity": entities[1].normalized_name})

    return rels


async def extract_relationships(
    structured_json: dict,
    entities: List[EntityCreate],
) -> List[Dict[str, str]]:
    """Extract relationships between entities."""
    client = get_anthropic_client()
    if client is None:
        return _extract_relationships_fallback(entities)

    entity_list = [{"type": e.type, "normalized_name": e.normalized_name} for e in entities]
    user_context = (
        f"STRUCTURED DOCUMENT DATA:\n{json.dumps(structured_json, indent=2)}\n\n"
        f"EXTRACTED ENTITIES:\n{json.dumps(entity_list, indent=2)}"
    )

    container = await call_llm_with_validation(
        system_prompt=RELATIONSHIP_SYSTEM_PROMPT.strip(),
        user_message=user_context,
        pydantic_schema=ExtractedRelationshipsContainer,
        client=client,
    )

    relationships = []
    for rel in container.relationships:
        relationships.append(
            {
                "from_entity": rel.from_entity,
                "relation": rel.relation,
                "to_entity": rel.to_entity,
            }
        )
    return relationships
