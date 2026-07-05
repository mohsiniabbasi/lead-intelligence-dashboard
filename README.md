# B2B Lead Intelligence Dashboard

A pipeline that turns a raw company list into a **ranked, filterable set of qualified leads**.
Source → enrich → score → deliver. Built as a portfolio demonstration of data-pipeline
+ LLM-enrichment + dashboard work.

![status](https://img.shields.io/badge/build-demo-blue)

## What it does
1. **Ingests** a list of companies (here: a synthetic dataset; in production: a client's approved feed or a public API).
2. **Enriches** each record — sector, size band, ICP-fit label and a short "why it fits".
3. **Scores** every lead 0–100 against an auditable ICP rubric.
4. **Dashboard** — searchable, filterable table + KPI cards + charts (score distribution, by sector, by size band).
5. **Exports** the qualified shortlist (score ≥ 75) as CSV, ready for outreach.

## How the score works (fully auditable)
| Signal | Max points |
|---|---|
| Target sector (SaaS / E-commerce / Prof-services / Financial) | 40 |
| Headcount band (mid-market 50–249 scores highest) | 30 |
| Target region (London / Manchester / Bristol / Leeds) | 20 |
| Has an online presence | 10 |

Fit label: **High** ≥ 75 · **Medium** ≥ 50 · **Low** < 50.

## Run it locally
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8010
# open http://localhost:8010
```

## Optional: LLM-written fit reasons
The scoring stays rule-based (auditable). If you want the one-line justification
written by Claude instead of the rule template:
```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
# then set use_llm=True in app/main.py where enrich() is called
```

## Data & privacy
Runs on **synthetic, fabricated company data** generated from fixed word lists
(`app/data.py`), using the reserved `.example` domain for all websites/emails.
**No real companies, personal emails, phone numbers, or private data** are used
or stored — zero privacy/data-protection risk. Point `app/data.py` at a real
approved source to run it on live data.

## Stack
Python · FastAPI · Chart.js · (optional) Claude for enrichment reasons.

---
*Demonstration build — not a paid client engagement. All data shown is synthetic.*
