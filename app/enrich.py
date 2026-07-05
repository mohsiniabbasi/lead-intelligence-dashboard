"""Enrichment + ICP scoring.

Two modes:

1. Default (offline, no API key): a transparent rule-based rubric enriches and
   scores each company. Deterministic, so results/screenshots are stable.

2. LLM mode (optional): if an ANTHROPIC_API_KEY is set and `use_llm=True`, the
   enrichment reason is written by Claude. The scoring rubric stays rule-based
   so scores remain auditable — the LLM adds the human-readable justification.

Swapping in a client's real data source only means replacing data.generate_*
with their approved feed; the scoring/enrichment layer is unchanged.
"""
from __future__ import annotations

import os

from .data import Company, size_band, is_target_sector, is_target_region

# Scoring weights (sum of maxes = 100) -- fully auditable.
_W_SECTOR = 40      # ICP sector match
_W_SIZE = 30        # target headcount band
_W_REGION = 20      # target region
_W_WEB = 10         # has a website / online presence


def _size_points(employees: int) -> int:
    # Mid-market (50-249) is the sweet spot for this ICP.
    band = size_band(employees)
    return {"Mid (50-249)": _W_SIZE,
            "Small (10-49)": int(_W_SIZE * 0.6),
            "Large (250+)": int(_W_SIZE * 0.4),
            "Micro (1-9)": int(_W_SIZE * 0.2)}[band]


def score_company(c: Company) -> int:
    score = 0
    if is_target_sector(c.sector):
        score += _W_SECTOR
    score += _size_points(c.employees)
    if is_target_region(c.region):
        score += _W_REGION
    if c.website:
        score += _W_WEB
    return min(score, 100)


def fit_label(score: int) -> str:
    if score >= 75:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def _rule_reason(c: Company, score: int) -> str:
    bits = []
    bits.append("target sector" if is_target_sector(c.sector) else f"non-core sector ({c.sector})")
    bits.append(f"{size_band(c.employees).split()[0].lower()} headcount")
    bits.append("in a target region" if is_target_region(c.region) else "outside core regions")
    lead = "Strong fit" if score >= 75 else "Partial fit" if score >= 50 else "Weak fit"
    return f"{lead}: {', '.join(bits)}."


def _llm_reason(c: Company, score: int) -> str:
    """Optional: ask Claude to phrase the justification. Falls back on any error."""
    try:
        from anthropic import Anthropic  # imported lazily so the app runs without it
        client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        prompt = (
            f"A lead-scoring rubric gave this company {score}/100 for our ICP "
            f"(mid-sized UK SaaS/e-commerce/professional-services firms in major cities).\n"
            f"Company: {c.name}, sector {c.sector}, {c.employees} staff, {c.region}.\n"
            "Write ONE short sentence (max 18 words) explaining the fit. No preamble."
        )
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=60,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception:
        return _rule_reason(c, score)


def enrich(c: Company, use_llm: bool = False) -> dict:
    score = score_company(c)
    reason = _llm_reason(c, score) if (use_llm and os.getenv("ANTHROPIC_API_KEY")) else _rule_reason(c, score)
    return {
        "score": score,
        "icp_fit": fit_label(score),
        "fit_reason": reason,
        "size_band": size_band(c.employees),
        "status": "New",
    }
