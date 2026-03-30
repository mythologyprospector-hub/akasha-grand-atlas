import csv
import pathlib

from common import normalize_url

ROOT = pathlib.Path(__file__).resolve().parents[1]

CANON = ROOT / "data" / "bookmarks.csv"
RANKED = ROOT / "reports" / "harvest-candidates-ranked.csv"
OUT = ROOT / "reports" / "bookmarks.auto-promoted.preview.csv"

CANON_FIELDS = [
    "name",
    "url",
    "category",
    "subcategory",
    "tags",
    "description",
    "free_tier",
    "catalog_or_supplier",
    "status",
    "last_checked",
    "replacement_url",
    "notes",
]

def load_csv(path: pathlib.Path):
    if not path.exists():
        raise SystemExit(f"Missing file: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def main():
    canon_rows = load_csv(CANON)
    ranked_rows = load_csv(RANKED)

    seen_urls = {normalize_url(r.get("url", "")) for r in canon_rows}
    promoted = []
    merged = list(canon_rows)

    for row in ranked_rows:
        if row.get("rank_bucket") != "auto_promote":
            continue

        norm = normalize_url(row.get("url", ""))
        if not norm or norm in seen_urls:
            continue

        new_row = {
            "name": row.get("name", "").strip(),
            "url": row.get("url", "").strip(),
            "category": row.get("category", "").strip() or "candidate",
            "subcategory": row.get("subcategory", "").strip() or "harvested",
            "tags": row.get("tags", "").strip(),
            "description": row.get("description", "").strip() or "auto-promoted from ranked harvest",
            "free_tier": row.get("free_tier", "").strip(),
            "catalog_or_supplier": row.get("catalog_or_supplier", "").strip(),
            "status": row.get("status", "").strip() or "unknown",
            "last_checked": row.get("last_checked", "").strip(),
            "replacement_url": row.get("replacement_url", "").strip(),
            "notes": f"auto_promoted rank_score={row.get('rank_score','')} source={row.get('source','')}".strip(),
        }

        merged.append(new_row)
        promoted.append(new_row)
        seen_urls.add(norm)

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CANON_FIELDS)
        w.writeheader()
        w.writerows(merged)

    print(f"Wrote {OUT}")
    print(f"Auto-promoted: {len(promoted)}")

if __name__ == "__main__":
    main()