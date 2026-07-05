"""B2B Lead Intelligence Dashboard — FastAPI backend.

Pipeline: generate/ingest companies -> enrich + score -> serve a filterable
dashboard + CSV export. Runs entirely on synthetic data (no private data).
"""
from __future__ import annotations

import csv
import io
from collections import Counter
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from .data import generate_companies, company_dict
from .enrich import enrich

app = FastAPI(title="Lead Intelligence Dashboard", version="1.0.0")

STATIC = Path(__file__).parent / "static"
QUALIFIED_THRESHOLD = 75

# Build the enriched dataset once at startup (the "pipeline run").
_companies = generate_companies(120)
LEADS: list[dict] = []
for _c in _companies:
    row = company_dict(_c)
    row.update(enrich(_c))          # set use_llm=True to have Claude write reasons
    LEADS.append(row)
LEADS.sort(key=lambda r: r["score"], reverse=True)

SECTORS = sorted({r["sector"] for r in LEADS})


def _filtered(query: str, sector: str, min_score: int, fit: str) -> list[dict]:
    q = query.lower().strip()
    out = []
    for r in LEADS:
        if q and q not in r["name"].lower() and q not in r["sector"].lower() and q not in r["region"].lower():
            continue
        if sector and r["sector"] != sector:
            continue
        if fit and r["icp_fit"] != fit:
            continue
        if r["score"] < min_score:
            continue
        out.append(r)
    return out


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/leads")
def api_leads(
    query: str = "",
    sector: str = "",
    min_score: int = Query(0, ge=0, le=100),
    fit: str = "",
):
    rows = _filtered(query, sector, min_score, fit)
    return JSONResponse({"count": len(rows), "sectors": SECTORS, "leads": rows})


@app.get("/api/stats")
def api_stats():
    total = len(LEADS)
    qualified = sum(1 for r in LEADS if r["score"] >= QUALIFIED_THRESHOLD)
    by_sector = Counter(r["sector"] for r in LEADS)
    by_band = Counter(r["size_band"] for r in LEADS)
    by_fit = Counter(r["icp_fit"] for r in LEADS)
    buckets = ["0-24", "25-49", "50-74", "75-100"]
    dist = {b: 0 for b in buckets}
    for r in LEADS:
        s = r["score"]
        dist[buckets[0] if s < 25 else buckets[1] if s < 50 else buckets[2] if s < 75 else buckets[3]] += 1
    return {
        "total": total,
        "qualified": qualified,
        "avg_score": round(sum(r["score"] for r in LEADS) / total, 1),
        "by_sector": dict(by_sector),
        "by_size_band": dict(by_band),
        "by_fit": dict(by_fit),
        "score_distribution": dist,
        "qualified_threshold": QUALIFIED_THRESHOLD,
    }


@app.get("/api/export.csv")
def export_csv(min_score: int = QUALIFIED_THRESHOLD):
    rows = [r for r in LEADS if r["score"] >= min_score]
    buf = io.StringIO()
    cols = ["name", "sector", "size_band", "region", "email", "website",
            "icp_fit", "score", "fit_reason", "status"]
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=qualified_leads.csv"},
    )
