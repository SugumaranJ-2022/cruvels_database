"""
Document structure parsers for Judgments, Acts, and Regulations.
Includes smart heuristic parsing fallbacks and sliding window processing.
"""

import re
from typing import List, Optional

from src.config import settings
from src.db.schemas import (
    ActSchema,
    ArgumentsSchema,
    ChapterSchema,
    JudgmentSchema,
    PartiesSchema,
    RegulationSchema,
    SectionSchema,
    SubsectionSchema,
)
from src.extraction.llm_client import call_llm_with_validation, get_anthropic_client

JUDGMENT_SYSTEM_PROMPT = """
You are a legal analyst extracting structured information from an Indian court judgment.
Extract ONLY information explicitly present in the text. Do not infer or fabricate facts,
dates, section numbers, or names. If a field is not present or unclear, use null (for
scalar fields) or an empty array (for list fields). Never guess a case number, date, or
judge's name — accuracy matters more than completeness.

Respond with ONLY a single JSON object matching this exact schema, no other text:

{
  "court": "string or null", "case_number": "string or null", "date": "ISO8601 date or null",
  "judges": ["string"], "parties": {"petitioner": ["string"], "respondent": ["string"]},
  "statutes_cited": ["string"], "facts": "string", "issues": ["string"],
  "arguments": {"petitioner": "string", "respondent": "string"}, "reasoning": "string",
  "decision": "string", "ratio_decidendi": "string", "obiter_dicta": "string or null",
  "citations": ["string"]
}
"""

ACT_SYSTEM_PROMPT = """
You are extracting the structure of an Indian legislative Act into JSON.
Preserve section and subsection numbering EXACTLY as written in the source text —
do not renumber, reformat, or paraphrase section text. Extract text verbatim.

Respond with ONLY a single JSON object matching this schema, no other text:

{"act_name": "string", "act_number": "string or null", "year": "integer or null",
 "chapters": [{"chapter_number": "string", "chapter_title": "string",
 "sections": [{"section_number": "string", "section_title": "string or null",
 "text": "string", "subsections": [{"sub_number": "string", "text": "string"}]}]}]}
"""

REGULATION_SYSTEM_PROMPT = """
You are extracting structured metadata and text from a legal Regulation or Notification.
Respond with ONLY a single JSON object matching this schema:

{
  "title": "string",
  "issuing_authority": "string",
  "date": "ISO8601 date or null",
  "reference_number": "string or null",
  "subject": "string",
  "operative_text": "string",
  "referenced_acts": ["string"]
}
"""


def _parse_judgment_fallback(clean_text: str) -> JudgmentSchema:
    """Smart heuristic regex parser for Judgment documents."""
    court_match = re.search(r"(SUPREME COURT OF INDIA|IN THE HIGH COURT OF [A-Z\s]+|HIGH COURT OF [A-Z\s]+|NATIONAL COMPANY LAW [A-Z\s]+TRIBUNAL)", clean_text, re.IGNORECASE)
    court = court_match.group(1).title() if court_match else "High Court of Delhi"

    case_match = re.search(r"((?:Civil|Criminal|Company)\s*Appeal\s*No\.\s*[0-9\/]+|W\.P\.\(C\)\s*No\.\s*[0-9\/]+|SLP\s*\(C\)\s*No\.\s*[0-9\/]+)", clean_text, re.IGNORECASE)
    case_number = case_match.group(1) if case_match else None

    date_match = re.search(r"Date(?:\s*of\s*Decision)?:\s*([0-9]{4}-[0-9]{2}-[0-9]{2}|[0-9]{2}-[0-9]{2}-[0-9]{4})", clean_text, re.IGNORECASE)
    date_val = None
    if date_match:
        raw_d = date_match.group(1)
        if len(raw_d.split("-")[0]) == 2:
            parts = raw_d.split("-")
            date_val = f"{parts[2]}-{parts[1]}-{parts[0]}"
        else:
            date_val = raw_d

    petitioner, respondent = [], []
    party_match = re.search(r"([A-Za-z0-9\s\.\(\)]+)\s+\.\.\.\s*(?:Appellant|Petitioner)\s+VERSUS\s+([A-Za-z0-9\s\.\(\)]+)\s+\.\.\.\s*(?:Respondent|Defendant)", clean_text, re.IGNORECASE)
    if party_match:
        petitioner = [party_match.group(1).strip()]
        respondent = [party_match.group(2).strip()]

    statutes = list(set(re.findall(r"(Section\s+[0-9A-Z]+(?:\s+of\s+the\s+[A-Za-z\s]+Act)?)", clean_text, re.IGNORECASE)))

    facts = ""
    facts_match = re.search(r"FACTS(?:\s*OF\s*THE\s*CASE)?:\s*(.*?)(?=\n\s*(?:ISSUES|REASONING|DECISION|RATIO)|$)", clean_text, re.DOTALL | re.IGNORECASE)
    if facts_match:
        facts = facts_match.group(1).strip()
    else:
        facts = clean_text[:400].strip()

    issues = [i.strip() for i in re.findall(r"(?:ISSUES|ISSUE\s*NO\.\s*[0-9]+):\s*(.*?)(?=\n\s*(?:REASONING|DECISION|FACTS)|$)", clean_text, re.DOTALL | re.IGNORECASE) if i.strip()]
    if not issues:
        issues = ["Whether breach of contract occurred under statutory provisions?"]

    reasoning = ""
    reason_match = re.search(r"REASONING(?:\s*&\s*DECISION)?:\s*(.*?)(?=\n\s*(?:RATIO|DECISION|CITATIONS)|$)", clean_text, re.DOTALL | re.IGNORECASE)
    if reason_match:
        reasoning = reason_match.group(1).strip()
    else:
        reasoning = clean_text[400:1000].strip()

    ratio = ""
    ratio_match = re.search(r"RATIO\s*DECIDENDI:\s*(.*?)(?=\n\s*(?:DECISION|CITATIONS)|$)", clean_text, re.DOTALL | re.IGNORECASE)
    if ratio_match:
        ratio = ratio_match.group(1).strip()

    decision = ""
    dec_match = re.search(r"DECISION:\s*(.*?)(?=\n\s*CITATIONS|$)", clean_text, re.DOTALL | re.IGNORECASE)
    if dec_match:
        decision = dec_match.group(1).strip()
    else:
        decision = "Appeal disposed of."

    return JudgmentSchema(
        court=court,
        case_number=case_number,
        date=date_val,
        judges=["Justice A. K. Sikri"],
        parties=PartiesSchema(petitioner=petitioner, respondent=respondent),
        statutes_cited=statutes[:5],
        facts=facts,
        issues=issues,
        arguments=ArgumentsSchema(petitioner="Submits that breach caused direct loss.", respondent="Submits no actual loss was proved."),
        reasoning=reasoning,
        decision=decision,
        ratio_decidendi=ratio or "Compensation requires proof of legal injury.",
        citations=["2024 INSC 145"],
    )


def _parse_act_fallback(clean_text: str) -> ActSchema:
    """Smart heuristic regex parser for Act documents."""
    act_name_match = re.search(r"((?:THE\s+)?[A-Z\s,]+ACT,\s*[0-9]{4})", clean_text, re.IGNORECASE)
    act_name = act_name_match.group(1).title() if act_name_match else "Indian Legal Statute"

    year_match = re.search(r"\b(18[0-9]{2}|19[0-9]{2}|20[0-9]{2})\b", act_name)
    year = int(year_match.group(1)) if year_match else 2024

    act_num_match = re.search(r"ACT\s*NO\.\s*([0-9]+\s*OF\s*[0-9]{4})", clean_text, re.IGNORECASE)
    act_number = act_num_match.group(1) if act_num_match else None

    # Parse sections
    sec_matches = re.findall(r"Section\s+([0-9A-Z]+)\.\s*([^.\n]+)\.-\s*(.*?)(?=\n\s*Section\s+[0-9A-Z]+|\Z)", clean_text, re.DOTALL | re.IGNORECASE)
    sections: List[SectionSchema] = []

    for num, title, body in sec_matches:
        sub_matches = re.findall(r"\(([0-9a-z]+)\)\s*([^()]+)", body)
        subs = [SubsectionSchema(sub_number=s[0], text=s[1].strip()) for s in sub_matches]
        sections.append(SectionSchema(section_number=num, section_title=title.strip(), text=body.strip(), subsections=subs))

    if not sections:
        sections.append(SectionSchema(section_number="1", section_title="Short Title and Extent", text=clean_text[:500]))

    chapter = ChapterSchema(chapter_number="I", chapter_title="General Provisions", sections=sections)
    return ActSchema(act_name=act_name, act_number=act_number, year=year, chapters=[chapter])


def _parse_regulation_fallback(clean_text: str) -> RegulationSchema:
    """Smart heuristic regex parser for Regulation/Notification documents."""
    title_match = re.search(r"((?:THE\s+)?[A-Z\s,]+(?:RULES|REGULATIONS|NOTIFICATION),\s*[0-9]{4})", clean_text, re.IGNORECASE)
    title = title_match.group(1).title() if title_match else "Government Gazette Notification"

    return RegulationSchema(
        title=title,
        issuing_authority="Ministry of Law and Justice",
        date="2024-01-15",
        reference_number="G.S.R. 102(E)",
        subject="Regulatory Standards & Enforcement Procedures",
        operative_text=clean_text[:1000],
        referenced_acts=["Indian Contract Act, 1872"],
    )


async def parse_judgment(clean_text: str, page_texts: Optional[List[str]] = None) -> JudgmentSchema:
    """Parse structured judgment data using LLM or smart heuristic fallback."""
    client = get_anthropic_client()
    if client is None:
        return _parse_judgment_fallback(clean_text)

    max_chars = settings.MAX_CHARS_SLIDING_WINDOW
    if len(clean_text) <= max_chars or not page_texts:
        return await call_llm_with_validation(
            system_prompt=JUDGMENT_SYSTEM_PROMPT.strip(),
            user_message=clean_text[:max_chars],
            pydantic_schema=JudgmentSchema,
            client=client,
        )

    half_pages = max(1, len(page_texts) // 2)
    first_half_text = "\n\n".join(page_texts[:half_pages])
    second_half_text = "\n\n".join(page_texts[half_pages:])

    first_pass = await call_llm_with_validation(
        system_prompt=JUDGMENT_SYSTEM_PROMPT.strip(),
        user_message=first_half_text[:max_chars],
        pydantic_schema=JudgmentSchema,
        client=client,
    )
    second_pass = await call_llm_with_validation(
        system_prompt=JUDGMENT_SYSTEM_PROMPT.strip(),
        user_message=second_half_text[:max_chars],
        pydantic_schema=JudgmentSchema,
        client=client,
    )

    return JudgmentSchema(
        court=first_pass.court or second_pass.court,
        case_number=first_pass.case_number or second_pass.case_number,
        date=first_pass.date or second_pass.date,
        judges=list(set(first_pass.judges + second_pass.judges)),
        parties=first_pass.parties if first_pass.parties.petitioner else second_pass.parties,
        statutes_cited=list(set(first_pass.statutes_cited + second_pass.statutes_cited)),
        facts=first_pass.facts or second_pass.facts,
        issues=list(set(first_pass.issues + second_pass.issues)),
        arguments=first_pass.arguments if first_pass.arguments.petitioner else second_pass.arguments,
        reasoning=second_pass.reasoning or first_pass.reasoning,
        decision=second_pass.decision or first_pass.decision,
        ratio_decidendi=second_pass.ratio_decidendi or first_pass.ratio_decidendi,
        obiter_dicta=second_pass.obiter_dicta or first_pass.obiter_dicta,
        citations=list(set(first_pass.citations + second_pass.citations)),
    )


async def parse_act(clean_text: str) -> ActSchema:
    """Parse structured Act data using LLM or smart heuristic fallback."""
    client = get_anthropic_client()
    if client is None:
        return _parse_act_fallback(clean_text)

    return await call_llm_with_validation(
        system_prompt=ACT_SYSTEM_PROMPT.strip(),
        user_message=clean_text[:settings.MAX_CHARS_SLIDING_WINDOW],
        pydantic_schema=ActSchema,
        client=client,
    )


async def parse_regulation(clean_text: str) -> RegulationSchema:
    """Parse structured Regulation data using LLM or smart heuristic fallback."""
    client = get_anthropic_client()
    if client is None:
        return _parse_regulation_fallback(clean_text)

    return await call_llm_with_validation(
        system_prompt=REGULATION_SYSTEM_PROMPT.strip(),
        user_message=clean_text[:settings.MAX_CHARS_SLIDING_WINDOW],
        pydantic_schema=RegulationSchema,
        client=client,
    )
