"""Synthetic company data generator.

Generates realistic-but-fictional companies for the demonstration. No real
company records, personal emails, or private data are used — every value here
is fabricated from fixed word lists with a fixed random seed, so the dataset is
reproducible (stable screenshots) and carries zero privacy risk.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, asdict

SEED = 42

# --- Fictional name building blocks -----------------------------------------
_PREFIX = [
    "North", "Bright", "Iron", "Blue", "Ever", "Oak", "Summit", "Vertex",
    "Harbour", "Silver", "Crest", "Meridian", "Cobalt", "Halcyon", "Quill",
    "Granite", "Aster", "Cedar", "Nimbus", "Foundry",
]
_SUFFIX = [
    "lane", "works", "field", "core", "bridge", "point", "wave", "forge",
    "path", "grove", "ridge", "loop", "gate", "haven", "stack",
]
_LEGAL = ["Ltd", "Group", "Solutions", "Partners", "Systems", "Studio", "Labs"]

SECTORS = [
    "SaaS", "E-commerce", "Professional Services", "Healthcare",
    "Manufacturing", "Construction", "Hospitality", "Logistics",
    "Financial Services", "Education",
]

REGIONS = [
    "London", "Manchester", "Birmingham", "Leeds", "Bristol",
    "Glasgow", "Sheffield", "Liverpool", "Nottingham", "Cardiff",
]

# ICP the demo scores against: mid-sized UK SaaS / e-commerce / prof-services.
_TARGET_SECTORS = {"SaaS", "E-commerce", "Professional Services", "Financial Services"}
_TARGET_REGIONS = {"London", "Manchester", "Bristol", "Leeds"}


@dataclass
class Company:
    id: int
    name: str
    sector: str
    employees: int
    region: str
    website: str
    email: str
    founded: int


def _slug(name: str) -> str:
    return "".join(c for c in name.lower() if c.isalnum())


def size_band(employees: int) -> str:
    if employees < 10:
        return "Micro (1-9)"
    if employees < 50:
        return "Small (10-49)"
    if employees < 250:
        return "Mid (50-249)"
    return "Large (250+)"


def generate_companies(n: int = 120) -> list[Company]:
    rng = random.Random(SEED)
    seen: set[str] = set()
    companies: list[Company] = []
    cid = 1
    while len(companies) < n:
        name = f"{rng.choice(_PREFIX)}{rng.choice(_SUFFIX)} {rng.choice(_LEGAL)}"
        if name in seen:
            continue
        seen.add(name)
        slug = _slug(name.split()[0] + name.split()[1])
        companies.append(
            Company(
                id=cid,
                name=name,
                sector=rng.choice(SECTORS),
                employees=rng.choice([4, 8, 15, 22, 40, 65, 90, 140, 210, 320, 600]),
                region=rng.choice(REGIONS),
                website=f"https://{slug}.example",           # .example = reserved, non-routable
                email=f"hello@{slug}.example",                # synthetic, not a real inbox
                founded=rng.randint(1998, 2023),
            )
        )
        cid += 1
    return companies


def is_target_sector(sector: str) -> bool:
    return sector in _TARGET_SECTORS


def is_target_region(region: str) -> bool:
    return region in _TARGET_REGIONS


def company_dict(c: Company) -> dict:
    d = asdict(c)
    d["size_band"] = size_band(c.employees)
    return d
