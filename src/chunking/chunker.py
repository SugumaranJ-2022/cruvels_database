"""
Hierarchical document chunking engine for multi-level vector and keyword index preparation.
"""

from typing import Any, Dict, List
import uuid

from src.db.schemas import KnowledgeChunkCreate


def build_chunks(
    document_id: uuid.UUID,
    doc_type: str,
    structured_json: Dict[str, Any],
    authority_score: float = 0.5,
    recency_score: float = 0.5,
) -> List[KnowledgeChunkCreate]:
    """
    Build hierarchical KnowledgeChunk structures from structured document JSON.
    """
    chunks: List[KnowledgeChunkCreate] = []

    # 1. Document summary chunk (level="document")
    doc_summary_lines = []
    if doc_type == "judgment":
        doc_summary_lines.append(f"Judgment of {structured_json.get('court', 'Court')}")
        if structured_json.get("case_number"):
            doc_summary_lines.append(f"Case No: {structured_json.get('case_number')}")
        if structured_json.get("ratio_decidendi"):
            doc_summary_lines.append(f"Ratio: {structured_json.get('ratio_decidendi')}")
    elif doc_type == "act":
        doc_summary_lines.append(f"Act: {structured_json.get('act_name', 'Statute')}")
        if structured_json.get("act_number"):
            doc_summary_lines.append(f"Act No: {structured_json.get('act_number')}")
    else:
        doc_summary_lines.append(f"Document Summary ({doc_type})")

    doc_summary_text = "\n".join(doc_summary_lines)

    doc_level_chunk = KnowledgeChunkCreate(
        document_id=document_id,
        hierarchical_level="document",
        section_type="other",
        content=doc_summary_text,
        importance_score=1.1,
        authority_score=authority_score,
        recency_score=recency_score,
    )
    chunks.append(doc_level_chunk)

    # 2. Document section chunks (level="section" or "subsection")
    if doc_type == "judgment":
        section_mappings = [
            ("facts", "facts", 1.0),
            ("issues", "issues", 1.0),
            ("reasoning", "reasoning", 1.3),
            ("ratio_decidendi", "ratio_decidendi", 1.5),
            ("decision", "decision", 1.4),
        ]

        for field_name, sec_type, importance in section_mappings:
            val = structured_json.get(field_name)
            if not val:
                continue

            if isinstance(val, list):
                content_str = "\n".join(f"- {item}" for item in val if item)
            else:
                content_str = str(val).strip()

            if content_str:
                chunk = KnowledgeChunkCreate(
                    document_id=document_id,
                    hierarchical_level="section",
                    section_type=sec_type,  # type: ignore
                    content=content_str,
                    importance_score=importance,
                    authority_score=authority_score,
                    recency_score=recency_score,
                )
                chunks.append(chunk)

    elif doc_type == "act":
        chapters = structured_json.get("chapters", [])
        for chap in chapters:
            chap_num = chap.get("chapter_number", "")
            chap_title = chap.get("chapter_title", "")
            chap_content = f"Chapter {chap_num}: {chap_title}".strip()

            # Chapter chunk (level="section")
            chap_chunk_id = uuid.uuid4()
            chap_chunk = KnowledgeChunkCreate(
                document_id=document_id,
                hierarchical_level="section",
                section_type="statute_section",
                content=chap_content,
                importance_score=1.2,
                authority_score=authority_score,
                recency_score=recency_score,
            )
            chunks.append(chap_chunk)

            # Section chunks (level="subsection", parent_chunk_id = chap_chunk)
            sections = chap.get("sections", [])
            for sec in sections:
                sec_num = sec.get("section_number", "")
                sec_title = sec.get("section_title") or ""
                sec_text = sec.get("text", "")

                sec_content_parts = [f"Section {sec_num}: {sec_title}".strip(), sec_text]
                for sub in sec.get("subsections", []):
                    sec_content_parts.append(f"({sub.get('sub_number', '')}) {sub.get('text', '')}")

                sec_content = "\n".join([p for p in sec_content_parts if p.strip()])

                sec_chunk = KnowledgeChunkCreate(
                    document_id=document_id,
                    hierarchical_level="subsection",
                    section_type="statute_section",
                    content=sec_content,
                    parent_chunk_id=chap_chunk_id,
                    importance_score=1.3,
                    authority_score=authority_score,
                    recency_score=recency_score,
                )
                chunks.append(sec_chunk)

    else:
        # Fallback / regulation chunks
        op_text = structured_json.get("operative_text") or str(structured_json)
        reg_chunk = KnowledgeChunkCreate(
            document_id=document_id,
            hierarchical_level="section",
            section_type="other",
            content=op_text,
            importance_score=1.0,
            authority_score=authority_score,
            recency_score=recency_score,
        )
        chunks.append(reg_chunk)

    return chunks
