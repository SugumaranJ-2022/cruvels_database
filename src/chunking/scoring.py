"""
Deterministic scoring logic for court authority and recency decay.
"""

from datetime import date
import math
from typing import Optional


def compute_authority_score(court: Optional[str]) -> float:
    """
    Compute rule-based court authority score.
    Supreme Court = 1.0, High Court = 0.7, Tribunal = 0.5, Other = 0.3.
    """
    if not court:
        return 0.3

    cleaned = court.lower()
    if "supreme court" in cleaned or "sc" in cleaned or "apex court" in cleaned:
        return 1.0
    elif "high court" in cleaned or "hc" in cleaned:
        return 0.7
    elif "tribunal" in cleaned or "nclt" in cleaned or "nclat" in cleaned or "aptel" in cleaned:
        return 0.5
    else:
        return 0.3


def compute_recency_score(doc_date: Optional[date], reference_date: Optional[date] = None, half_life_years: float = 10.0) -> float:
    """
    Compute exponential decay recency score with a configurable half-life (default 10 years).
    """
    if doc_date is None:
        return 0.5

    if reference_date is None:
        reference_date = date.today()

    days_elapsed = (reference_date - doc_date).days
    if days_elapsed < 0:
        return 1.0

    years_elapsed = days_elapsed / 365.25
    decay_score = math.pow(2.0, -years_elapsed / half_life_years)
    return max(0.01, min(1.0, round(decay_score, 4)))
