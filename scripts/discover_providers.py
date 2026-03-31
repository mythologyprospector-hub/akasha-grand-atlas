import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

RANKED_INPUT = REPORTS / "harvest-candidates-ranked.csv"
HARVEST_INPUT = REPORTS / "harvest-candidates-v3.csv"
OUTPUT = REPORTS / "api_candidates.csv"

API_KEYWORDS = {
    "api",
    "endpoint",
    "rest",
    "graphql",
    "dataset",
    "data portal",
    "open data",
    "developer api",
    "developer",
    "feed",
    "json feed",
    "rss",
}

DATA_HINTS = {
    "weather",
    "earthquake",
    "satellite",
    "solar",
    "space",
    "ocean",
    "tide",
    "wildlife",
    "astronomy",
    "climate",
    "geo",
    "geospatial",
    "mapping",
    "elevation",
    "radar",
    "storm",
    "lightning",
    "seismic",
    "biodiversity",
    "fungi",
    "mycology",
    "forestry",
}

HIGH_VALUE_DOMAINS = {
    "api.nasa.gov",
    "api.weather.gov",
    "earthquake.usgs.gov",
    "api.gbif.org",
    "opentopodata.org",
    "marine-api.open-meteo.com",
    "api.open-meteo.com",
    "sunrise-sunset.org",
}

PROVIDER_TYPE_HINTS = {
    "weather": "environmental_api",
    "earthquake": "geophysical_api",
    "solar": "astronomy_api",
    "space": "astronomy_api",
    "astronomy": "astronomy_api",
    "tide": "marine_api",
    "ocean": "marine_api",
    "wildlife": "ecology_api",
    "biodiversity": "ecology_api",
    "fungi": "ecology_api",
    "mycology": "ecology_api",
    "forestry": "ecology_api",
    "geo": "geospatial_api",
    "geospatial": "geospatial_api",
    "mapping": "geospatial_api",
    "elevation": "geospatial_api",
    "radar": "environmental_api",
    "storm": "environmental_api",
    "lightning": "environmental_api",
    "seismic": "geophysical_api",
}


def choose_input_file() -> Path:
    if RANKED_INPUT.exists():
        return RANKED_INPUT
    if HARVEST_INPUT.exists():
        return HARVEST_INPUT

    raise SystemExit(
        "No harvest input found.\n"
        "Run one of these first:\n"
        "  python scripts/harvest_v3.py\n"
        "  python scripts/rank_candidates.py"
    )


def text_blob(row: dict) -> str:
    bits = [
        row.get("name", ""),
        row.get("description", ""),
        row.get("category", ""),
        row.get("subcategory", ""),
        row.get("tags", ""),
        row.get("source", ""),
        row.get("url", ""),
    ]
    return " ".join(str(x) for x in bits if x).lower()


def detect_provider_type(blob: str) -> str:
    for hint, provider_type in PROVIDER_TYPE_HINTS.items():
        if hint in blob:
            return provider_type
    return "api"


def score_row(row: dict, blob: str) -> float:
    score = 0.0
    url = (row.get("url") or "").lower()

    if any(k in blob for k in API_KEYWORDS):
        score += 0.45

    if any(k in blob for k in DATA_HINTS):
        score += 0.25

    if any(domain in url for domain in HIGH_VALUE_DOMAINS):
        score += 0.20

    if "github.com" in url:
        score += 0.05

    try:
        rank_score = float(row.get("rank_score", "") or 0)
        score += min(rank_score / 1000.0, 0.10)
    except ValueError:
        pass

    return round(min(score, 0.99), 2)


def classify(row: dict) -> dict | None:
    blob = text_blob(row)
    url = row.get("url", "")

    if not url:
        return None

    looks_like_provider = (
        any(k in blob for k in API_KEYWORDS)
        or any(k in blob for k in DATA_HINTS)
        or any(domain in url.lower() for domain in HIGH_VALUE_DOMAINS)
    )

    if not looks_like_provider:
        return None

    provider_type = detect_provider_type(blob)
    score = score_row(row, blob)

    return {
        "name": row.get("name", ""),
        "url": url,
        "description": row.get("description", ""),
        "provider_type": provider_type,
        "relevance_score": score,
        "category": row.get("category", ""),
        "subcategory": row.get("subcategory", ""),
        "source": row.get("source", ""),
        "tags": row.get("tags", ""),
        "rank_score": row.get("rank_score", ""),
        "akasha_status": "candidate",
    }


def dedupe(rows: list[dict]) -> list[dict]:
    seen = set()
    out = []

    for row in sorted(rows, key=lambda r: float(r["relevance_score"]), reverse=True):
        key = row["url"].rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(row)

    return out


def main() -> None:
    input_file = choose_input_file()

    with input_file.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        providers = [p for row in reader if (p := classify(row))]

    providers = dedupe(providers)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "url",
                "description",
                "provider_type",
                "relevance_score",
                "category",
                "subcategory",
                "source",
                "tags",
                "rank_score",
                "akasha_status",
            ],
        )
        writer.writeheader()
        writer.writerows(providers)

    print(f"input: {input_file}")
    print(f"providers discovered: {len(providers)}")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
