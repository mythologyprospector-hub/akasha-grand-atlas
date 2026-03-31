import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

INPUT = REPORTS / "api_candidates.csv"
OUTPUT = REPORTS / "akasha_provider_shortlist.csv"

TARGET_PROVIDER_TYPES = {
    "environmental_api",
    "astronomy_api",
    "marine_api",
    "ecology_api",
    "geospatial_api",
    "geophysical_api",
    "api",
}

PREFERRED_KEYWORDS = {
    "weather": 0.20,
    "sunrise": 0.18,
    "sunset": 0.18,
    "solar": 0.18,
    "moon": 0.18,
    "lunar": 0.18,
    "earthquake": 0.18,
    "seismic": 0.18,
    "tide": 0.18,
    "ocean": 0.12,
    "marine": 0.12,
    "timezone": 0.20,
    "geo": 0.10,
    "geospatial": 0.12,
    "mapping": 0.10,
    "elevation": 0.12,
    "climate": 0.12,
    "storm": 0.12,
    "lightning": 0.12,
    "astronomy": 0.15,
    "space": 0.10,
    "wildlife": 0.10,
    "biodiversity": 0.10,
    "fungi": 0.10,
    "mycology": 0.10,
    "forestry": 0.10,
}

DOMAIN_BONUSES = {
    "api.weather.gov": 0.25,
    "api.nasa.gov": 0.25,
    "earthquake.usgs.gov": 0.25,
    "api.open-meteo.com": 0.22,
    "marine-api.open-meteo.com": 0.22,
    "sunrise-sunset.org": 0.20,
    "api.gbif.org": 0.20,
    "opentopodata.org": 0.18,
}

AKASHA_FIRST_LANES = {
    "weather": "time_nexus",
    "sunrise": "time_nexus",
    "sunset": "time_nexus",
    "solar": "time_nexus",
    "moon": "time_nexus",
    "lunar": "time_nexus",
    "timezone": "time_nexus",
    "tide": "time_nexus",
    "ocean": "time_nexus",
    "earthquake": "events",
    "seismic": "events",
    "wildlife": "events",
    "biodiversity": "events",
    "fungi": "events",
    "mycology": "events",
    "forestry": "events",
    "climate": "events",
    "storm": "events",
    "lightning": "events",
    "geo": "apis",
    "geospatial": "apis",
    "mapping": "apis",
    "elevation": "apis",
    "astronomy": "apis",
    "space": "apis",
}


def load_candidates() -> list[dict]:
    if not INPUT.exists():
        raise SystemExit(
            f"Missing input: {INPUT}\n"
            "Run this first:\n"
            "  python scripts/discover_providers.py"
        )

    with INPUT.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def text_blob(row: dict) -> str:
    parts = [
        row.get("name", ""),
        row.get("description", ""),
        row.get("provider_type", ""),
        row.get("category", ""),
        row.get("subcategory", ""),
        row.get("source", ""),
        row.get("tags", ""),
        row.get("url", ""),
    ]
    return " ".join(str(x) for x in parts if x).lower()


def infer_akasha_lane(blob: str) -> str:
    lane_scores = {
        "time_nexus": 0,
        "events": 0,
        "apis": 0,
    }

    for keyword, lane in AKASHA_FIRST_LANES.items():
        if keyword in blob:
            lane_scores[lane] += 1

    best_lane = max(lane_scores, key=lane_scores.get)
    return best_lane if lane_scores[best_lane] > 0 else "apis"


def akasha_score(row: dict) -> float:
    blob = text_blob(row)
    score = 0.0

    try:
        score += float(row.get("relevance_score", "") or 0)
    except ValueError:
        pass

    provider_type = (row.get("provider_type") or "").strip()
    if provider_type in TARGET_PROVIDER_TYPES:
        score += 0.15

    for keyword, bonus in PREFERRED_KEYWORDS.items():
        if keyword in blob:
            score += bonus

    url = (row.get("url") or "").lower()
    for domain, bonus in DOMAIN_BONUSES.items():
        if domain in url:
            score += bonus

    lane = infer_akasha_lane(blob)
    if lane == "time_nexus":
        score += 0.10
    elif lane == "events":
        score += 0.06
    elif lane == "apis":
        score += 0.04

    return round(min(score, 1.99), 2)


def shortlist(rows: list[dict]) -> list[dict]:
    out = []

    for row in rows:
        blob = text_blob(row)
        lane = infer_akasha_lane(blob)
        score = akasha_score(row)

        # Hard filter: keep only fairly relevant sources
        if score < 0.75:
            continue

        new_row = dict(row)
        new_row["akasha_lane"] = lane
        new_row["akasha_priority_score"] = score
        new_row["akasha_status"] = new_row.get("akasha_status", "") or "candidate"
        out.append(new_row)

    out.sort(
        key=lambda r: (
            {"time_nexus": 0, "events": 1, "apis": 2}.get(r["akasha_lane"], 9),
            -float(r["akasha_priority_score"]),
            r.get("name", "").lower(),
        )
    )
    return out


def main() -> None:
    rows = load_candidates()
    selected = shortlist(rows)

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
                "akasha_priority_score",
                "akasha_lane",
                "category",
                "subcategory",
                "source",
                "tags",
                "rank_score",
                "akasha_status",
            ],
        )
        writer.writeheader()
        writer.writerows(selected)

    lane_counts = {}
    for row in selected:
        lane_counts[row["akasha_lane"]] = lane_counts.get(row["akasha_lane"], 0) + 1

    print(f"input: {INPUT}")
    print(f"shortlist size: {len(selected)}")
    for lane, count in sorted(lane_counts.items()):
        print(f"  {lane}: {count}")
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    main()
