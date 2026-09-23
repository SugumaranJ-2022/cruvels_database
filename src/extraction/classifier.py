"""
Document classification module using LLM zero-shot prompt with text heuristic fallback.
"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.models import LowConfidenceQueue
from src.db.schemas import DocClassification
from src.extraction.llm_client import call_llm_with_validation, get_anthropic_client

CLASSIFIER_SYSTEM_PROMPT = """
You are a legal document classifier for an Indian legal knowledge base.
Classify the given document into exactly one of the 13 Phase-1 categories. Respond with ONLY a JSON object.

Types:
- "constitution": Constitution of India text, schedules, amendments, fundamental rights/duties
- "act": Current major legislative act or statute (e.g. BNS, BNSS, BSA, Companies Act, Contract Act, DPDP)
- "legacy_statute": Historical / repealed acts (e.g. IPC 1860, CrPC 1973, Evidence Act 1872)
- "regulation": Subordinate rules, regulations, statutory authority rules
- "judgment": Supreme Court or High Court judicial decisions
- "definition": Legal definitions collection
- "doctrine": Legal principles and doctrines (e.g., Natural Justice, Res Judicata, Basic Structure)
- "procedure": Procedural guides for civil/criminal/bail/appeals/writs
- "form": Legal application forms and reference formats
- "template": Standard legal document templates (NDA, Legal Notice, Agreement, Lease, POA)
- "notification": Government gazette notifications, circulars, CERT-In directions
- "citation_crossref": Legal cross-reference indices and citation mappings
- "order": Administrative orders
- "unknown": Unclassified document

Output schema:
{"doc_type": "judgment | act | constitution | legacy_statute | regulation | definition | doctrine | procedure | form | template | notification | citation_crossref | order | unknown", "confidence": 0.0-1.0, "reasoning": "one short sentence"}
"""


def _classify_fallback(text: str) -> DocClassification:
    """Heuristic fallback classification based on text content and keywords."""
    upper = text.upper()
    if "CONSTITUTION OF INDIA" in upper or "ARTICLE 21" in upper or "SCHEDULE OF THE CONSTITUTION" in upper or "FUNDAMENTAL RIGHTS" in upper:
        return DocClassification(doc_type="constitution", confidence=0.98, reasoning="Identified Constitutional material")
    elif "BHARATIYA NYAYA SANHITA" in upper or "BHARATIYA NAGARIK SURAKSHA" in upper or "BHARATIYA SAKSHYA" in upper or "COMPANIES ACT, 2013" in upper or "CONTRACT ACT, 1872" in upper or "DIGITAL PERSONAL DATA PROTECTION" in upper:
        return DocClassification(doc_type="act", confidence=0.96, reasoning="Identified Major Current Statute")
    elif "INDIAN PENAL CODE, 1860" in upper or "CODE OF CRIMINAL PROCEDURE, 1973" in upper or "INDIAN EVIDENCE ACT, 1872" in upper or "REPEALED" in upper:
        return DocClassification(doc_type="legacy_statute", confidence=0.95, reasoning="Identified Legacy Statute")
    elif "GAZETTE OF INDIA" in upper or "CERT-IN" in upper or "RBI/202" in upper or "SEBI/HO" in upper or "NOTIFICATION" in upper:
        return DocClassification(doc_type="notification", confidence=0.94, reasoning="Identified Government Notification/Direction")
    elif "RULE" in upper and ("REGULATION" in upper or "INTERMEDIARY GUIDELINES" in upper or "E-COMMERCE" in upper):
        return DocClassification(doc_type="regulation", confidence=0.93, reasoning="Identified Rules & Regulations")
    elif "LEGAL DOCTRINE" in upper or "BASIC STRUCTURE" in upper or "RES JUDICATA" in upper or "NATURAL JUSTICE" in upper or "AUDI ALTERAM PARTEM" in upper:
        return DocClassification(doc_type="doctrine", confidence=0.96, reasoning="Identified Legal Doctrine / Principle")
    elif "LEGAL DEFINITION" in upper or "DEFINED UNDER SECTION" in upper or "MEANS AND INCLUDES" in upper:
        return DocClassification(doc_type="definition", confidence=0.92, reasoning="Identified Legal Definition")
    elif "PROCEDURAL STEP" in upper or "BAIL PROCEDURE" in upper or "WRIT PETITION PROCEDURE" in upper or "CIVIL TRIAL STAGES" in upper:
        return DocClassification(doc_type="procedure", confidence=0.93, reasoning="Identified Legal Procedure Guide")
    elif "APPLICATION FOR BAIL" in upper or "FORM NO." in upper or "MEMORANDUM OF APPEAL" in upper or "AFFIDAVIT FORMAT" in upper:
        return DocClassification(doc_type="form", confidence=0.94, reasoning="Identified Legal Form / Application Format")
    elif "NON-DISCLOSURE AGREEMENT" in upper or "LEGAL NOTICE" in upper or "LEASE AGREEMENT" in upper or "POWER OF ATTORNEY" in upper or "MEMORANDUM OF UNDERSTANDING" in upper:
        return DocClassification(doc_type="template", confidence=0.95, reasoning="Identified Legal Document Template")
    elif "CITATION CROSS-REFERENCE" in upper or "CITES ->" in upper or "RELATIONAL GRAPH" in upper:
        return DocClassification(doc_type="citation_crossref", confidence=0.95, reasoning="Identified Citation Index")
    elif "IN THE HIGH COURT" in upper or "SUPREME COURT OF INDIA" in upper or "VERSUS" in upper or "APPELLANT" in upper:
        return DocClassification(doc_type="judgment", confidence=0.98, reasoning="Identified Judicial Judgment")
    elif "BE IT ENACTED" in upper or "CHAPTER I" in upper or "SHORT TITLE" in upper:
        return DocClassification(doc_type="act", confidence=0.95, reasoning="Identified Legislative Act")
    else:
        return DocClassification(doc_type="judgment", confidence=0.85, reasoning="Defaulted to judgment classification")


async def classify_document(
    clean_text: str,
    session: Optional[AsyncSession] = None,
    document_id: Optional[str] = None,
) -> DocClassification:
    """
    Classify clean text into document types using LLM or smart heuristic fallback.
    """
    client = get_anthropic_client()
    if client is None:
        classification = _classify_fallback(clean_text)
    else:
        snippet = clean_text[:2000]
        classification = await call_llm_with_validation(
            system_prompt=CLASSIFIER_SYSTEM_PROMPT.strip(),
            user_message=snippet,
            pydantic_schema=DocClassification,
            client=client,
        )

    if classification.confidence < 0.6 and session is not None:
        queue_entry = LowConfidenceQueue(
            document_id=document_id,
            doc_type=classification.doc_type,
            confidence=classification.confidence,
            reasoning=classification.reasoning,
            clean_text_snippet=clean_text[:500],
        )
        session.add(queue_entry)
        await session.flush()

    return classification
