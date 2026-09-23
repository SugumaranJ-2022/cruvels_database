"""
Unit tests for hierarchical chunker, authority scoring, and recency scoring.
"""

from datetime import date, timedelta
import uuid

from src.chunking.chunker import build_chunks
from src.chunking.scoring import compute_authority_score, compute_recency_score


def test_compute_authority_score():
    assert compute_authority_score("Supreme Court of India") == 1.0
    assert compute_authority_score("Delhi High Court") == 0.7
    assert compute_authority_score("NCLAT New Delhi") == 0.5
    assert compute_authority_score("District Court") == 0.3
    assert compute_authority_score(None) == 0.3


def test_compute_recency_score():
    today = date.today()
    assert compute_recency_score(today, reference_date=today) == 1.0

    ten_years_ago = today - timedelta(days=3652)
    score_10y = compute_recency_score(ten_years_ago, reference_date=today)
    assert 0.45 <= score_10y <= 0.55

    twenty_years_ago = today - timedelta(days=7305)
    score_20y = compute_recency_score(twenty_years_ago, reference_date=today)
    assert 0.20 <= score_20y <= 0.30

    assert compute_recency_score(None) == 0.5


def test_build_judgment_chunks():
    doc_id = uuid.uuid4()
    structured = {
        "court": "Supreme Court of India",
        "case_number": "Civil Appeal 1234/2024",
        "facts": "The appellant entered into a contract...",
        "issues": ["Whether Section 73 applies?"],
        "reasoning": "The court analyzed Section 73 of Contract Act...",
        "ratio_decidendi": "Breach of contract requires proof of actual loss.",
        "decision": "Appeal allowed.",
    }

    chunks = build_chunks(
        document_id=doc_id,
        doc_type="judgment",
        structured_json=structured,
        authority_score=1.0,
        recency_score=0.9,
    )

    levels = [c.hierarchical_level for c in chunks]
    sec_types = [c.section_type for c in chunks]

    assert "document" in levels
    assert "section" in levels
    assert "facts" in sec_types
    assert "issues" in sec_types
    assert "reasoning" in sec_types
    assert "ratio_decidendi" in sec_types
    assert "decision" in sec_types


def test_build_act_chunks_hierarchy():
    doc_id = uuid.uuid4()
    structured = {
        "act_name": "Indian Contract Act, 1872",
        "act_number": "9",
        "year": 1872,
        "chapters": [
            {
                "chapter_number": "VI",
                "chapter_title": "Of the Consequences of Breach of Contract",
                "sections": [
                    {
                        "section_number": "73",
                        "section_title": "Compensation for loss or damage caused by breach of contract",
                        "text": "When a contract has been broken...",
                        "subsections": [{"sub_number": "1", "text": "Compensation is recoverable."}],
                    }
                ],
            }
        ],
    }

    chunks = build_chunks(
        document_id=doc_id,
        doc_type="act",
        structured_json=structured,
    )

    doc_chunks = [c for c in chunks if c.hierarchical_level == "document"]
    chap_chunks = [c for c in chunks if c.hierarchical_level == "section"]
    sec_chunks = [c for c in chunks if c.hierarchical_level == "subsection"]

    assert len(doc_chunks) == 1
    assert len(chap_chunks) == 1
    assert len(sec_chunks) == 1
    assert sec_chunks[0].parent_chunk_id is not None
