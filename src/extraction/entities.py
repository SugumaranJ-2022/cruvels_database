"""
Entity extraction and canonical lookup table normalization module.
Includes heuristic text entity extraction fallback.
"""

import json
import re
from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import CanonicalEntity
from src.db.schemas import EntityCreate, ExtractedEntitiesContainer
from src.extraction.llm_client import call_llm_with_validation, get_anthropic_client

ENTITY_SYSTEM_PROMPT = """
Extract all named legal entities from the structured document data below.
Normalize entity names using the provided canonical lookup table where a match exists;
otherwise use your best normalized form. Do not invent entities not present in the text.

Entity types: act, section, constitution_article, schedule, amendment, case, court, judge, party, legal_concept, legal_doctrine, procedure, form_template, definition

Respond with ONLY a JSON object:
{"entities": [{"type": "...", "name": "...", "normalized_name": "..."}]}
"""


async def get_canonical_lookup(session: Optional[AsyncSession] = None) -> Dict[str, Dict[str, str]]:
    """Fetch canonical entity normalization lookup dictionary."""
    lookup: Dict[str, Dict[str, str]] = {
        "section": {
            "sec. 73": "Section 73",
            "section 73": "Section 73",
            "s.73": "Section 73",
            "sec. 74": "Section 74",
            "section 74": "Section 74",
            "s.74": "Section 74",
            "sec. 138": "Section 138",
            "section 138": "Section 138",
            "sec. 300": "Section 300",
            "section 300": "Section 300",
        },
        "act": {
            "contract act": "Indian Contract Act, 1872",
            "indian contract act": "Indian Contract Act, 1872",
            "ipc": "Indian Penal Code, 1860",
            "crpc": "Code of Criminal Procedure, 1973",
            "arbitration act": "Arbitration and Conciliation Act, 1996",
            "ni act": "Negotiable Instruments Act, 1881",
            "bns": "Bharatiya Nyaya Sanhita, 2023",
            "bnss": "Bharatiya Nagarik Suraksha Sanhita, 2023",
            "bsa": "Bharatiya Sakshya Adhiniyam, 2023",
            "dpdp": "Digital Personal Data Protection Act, 2023",
        },
    }

    if session is not None:
        try:
            stmt = select(CanonicalEntity)
            result = await session.execute(stmt)
            rows = result.scalars().all()

            for row in rows:
                if row.entity_type not in lookup:
                    lookup[row.entity_type] = {}
                lookup[row.entity_type][row.canonical_name.lower()] = row.canonical_name
                aliases = row.aliases if isinstance(row.aliases, list) else []
                for alias in aliases:
                    lookup[row.entity_type][alias.lower()] = row.canonical_name
        except Exception:
            pass

    return lookup


def normalize_entity_name(entity_type: str, raw_normalized: str, canonical_lookup: Dict[str, Dict[str, str]]) -> str:
    """Normalize entity name against the canonical lookup dictionary."""
    cleaned_key = raw_normalized.strip().lower()
    type_lookup = canonical_lookup.get(entity_type.lower(), {})

    if cleaned_key in type_lookup:
        return type_lookup[cleaned_key]

    for alias, canonical_name in type_lookup.items():
        if alias in cleaned_key or cleaned_key in alias:
            return canonical_name

    words = raw_normalized.strip().split()
    return " ".join(words).title() if words else raw_normalized.strip()


def _extract_entities_fallback(structured_json: dict, canonical_lookup: Dict[str, Dict[str, str]]) -> List[EntityCreate]:
    """Contextual fallback entity extractor."""
    entities: List[EntityCreate] = []

    # Court
    court = structured_json.get("court")
    if court:
        entities.append(EntityCreate(type="court", name=court, normalized_name=court))

    # Case Number
    case_num = structured_json.get("case_number")
    if case_num:
        entities.append(EntityCreate(type="case", name=case_num, normalized_name=case_num))

    # Act Name
    act_name = structured_json.get("act_name")
    if act_name:
        entities.append(EntityCreate(type="act", name=act_name, normalized_name=act_name))

    # Judges
    for judge in structured_json.get("judges", []):
        entities.append(EntityCreate(type="judge", name=judge, normalized_name=judge))

    # Parties
    parties = structured_json.get("parties", {})
    if isinstance(parties, dict):
        for p in parties.get("petitioner", []):
            entities.append(EntityCreate(type="party", name=p, normalized_name=p))
        for r in parties.get("respondent", []):
            entities.append(EntityCreate(type="party", name=r, normalized_name=r))

    # Statutes & Sections & Constitution Articles
    for stat in structured_json.get("statutes_cited", []):
        if "Article" in stat:
            entities.append(EntityCreate(type="constitution_article", name=stat, normalized_name=stat))
        elif "Section" in stat or "Sec" in stat or "S." in stat:
            entities.append(EntityCreate(type="section", name=stat, normalized_name=stat))
        elif "Act" in stat or "Code" in stat or "Sanhita" in stat or "Adhiniyam" in stat:
            entities.append(EntityCreate(type="act", name=stat, normalized_name=stat))

    # Text body analysis for doctrines, definitions, procedures, forms
    full_str = json.dumps(structured_json).lower()

    doctrines = [
        ("basic structure", "Basic Structure Doctrine"),
        ("natural justice", "Natural Justice"),
        ("res judicata", "Res Judicata"),
        ("stare decisis", "Stare Decisis"),
        ("presumption of innocence", "Presumption of Innocence"),
        ("audi alteram partem", "Audi Alteram Partem"),
        ("nemo judex", "Nemo Judex in Causa Sua"),
        ("proportionality", "Doctrine of Proportionality"),
        ("separation of powers", "Separation of Powers"),
        ("legitimate expectation", "Legitimate Expectation"),
        ("promissory estoppel", "Promissory Estoppel"),
    ]

    for term, doct_name in doctrines:
        if term in full_str:
            entities.append(EntityCreate(type="legal_doctrine", name=doct_name, normalized_name=doct_name))

    if "bail application" in full_str or "writ petition" in full_str or "affidavit format" in full_str:
        entities.append(EntityCreate(type="form_template", name="Standard Court Form", normalized_name="Standard Court Form"))

    if "procedural step" in full_str or "filing procedure" in full_str or "civil proceedings" in full_str:
        entities.append(EntityCreate(type="procedure", name="Legal Procedure Flow", normalized_name="Legal Procedure Flow"))

    if not entities:
        entities.append(EntityCreate(type="legal_concept", name="Legal Material", normalized_name="Legal Material"))

    return entities


async def extract_entities(
    structured_json: dict,
    canonical_lookup: Optional[Dict[str, Dict[str, str]]] = None,
    session: Optional[AsyncSession] = None,
) -> List[EntityCreate]:
    """Extract entities from structured JSON document."""
    if canonical_lookup is None:
        canonical_lookup = await get_canonical_lookup(session)

    client = get_anthropic_client()
    if client is None:
        raw_entities = _extract_entities_fallback(structured_json, canonical_lookup)
    else:
        user_context = (
            f"STRUCTURED DOCUMENT DATA:\n{json.dumps(structured_json, indent=2)}\n\n"
            f"CANONICAL LOOKUP TABLE ALIASES:\n{json.dumps(canonical_lookup, indent=2)}"
        )
        container = await call_llm_with_validation(
            system_prompt=ENTITY_SYSTEM_PROMPT.strip(),
            user_message=user_context,
            pydantic_schema=ExtractedEntitiesContainer,
            client=client,
        )
        raw_entities = [EntityCreate(type=e.type, name=e.name, normalized_name=e.normalized_name) for e in container.entities]

    final_entities: List[EntityCreate] = []
    seen_keys = set()

    for item in raw_entities:
        canonical_name = normalize_entity_name(
            entity_type=item.type,
            raw_normalized=item.normalized_name,
            canonical_lookup=canonical_lookup,
        )
        unique_key = (item.type.lower(), canonical_name.lower())
        if unique_key not in seen_keys:
            seen_keys.add(unique_key)
            final_entities.append(
                EntityCreate(
                    type=item.type,
                    name=item.name,
                    normalized_name=canonical_name,
                )
            )

    return final_entities
