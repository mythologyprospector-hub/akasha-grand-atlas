import csv
import pathlib
import sys

from common import normalize_url

ROOT = pathlib.Path(__file__).resolve().parents[1]

CANON = ROOT / "data" / "bookmarks.csv"
CANDIDATES = ROOT / "reports" / "harvest-candidates-v3.csv"
OUTPUT = ROOT / "reports" / "bookmarks.promoted.preview.csv"

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

def load_csv(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Missing file: {path}")
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def canon_keys(rows: list[dict]) -> set[tuple[str, str]]:
    keys = set()
    for row in rows:
        keys.add((
            row.get("name", "").strip().lower(),
            normalize_url(row.get("url", "")),
        ))
    return keys

def normalize_candidate_row(row: dict) -> dict:
    notes = (row.get("notes", "") or "").strip()
    source = (row.get("source", "") or "").strip()
    confidence = (row.get("confidence", "") or "").strip()

    extra = []
    if notes:
        extra.append(notes)
    if source:
        extra.append(f"source={source}")
    if confidence:
        extra.append(f"confidence={confidence}")

    return {
        "name": row.get("name", "").strip(),
        "url": row.get("url", "").strip(),
        "category": row.get("category", "").strip() or "candidate",
        "subcategory": row.get("subcategory", "").strip() or "harvested",
        "tags": row.get("tags", "").strip(),
        "description": row.get("description", "").strip() or "promoted from harvest candidates",
        "free_tier": row.get("free_tier", "").strip(),
        "catalog_or_supplier": row.get("catalog_or_supplier", "").strip(),
        "status": row.get("status", "").strip() or "unknown",
        "last_checked": row.get("last_checked", "").strip(),
        "replacement_url": row.get("replacement_url", "").strip(),
        "notes": " | ".join([x for x in extra if x]),
    }

def parse_args(argv: list[str]) -> tuple[int, set[str], bool]:
    """
    Usage examples:

    python scripts/promote_candidates.py
    python scripts/promote_candidates.py --min-confidence 70
    python scripts/promote_candidates.py --url https://example.com
    python scripts/promote_candidates.py --url https://a.com --url https://b.com
    python scripts/promote_candidates.py --min-confidence 75 --write
    """
    min_confidence = 0
    urls = set()
    write_mode = False

    i = 0
    while i < len(argv):
        arg = argv[i]

        if arg == "--min-confidence":
            if i + 1 >= len(argv):
                raise SystemExit("--min-confidence requires a value")
            min_confidence = int(argv[i + 1])
            i += 2
            continue

        if arg == "--url":
            if i + 1 >= len(argv):
                raise SystemExit("--url requires a value")
            urls.add(normalize_url(argv[i + 1]))
            i += 2
            continue

        if arg == "--write":
            write_mode = True
            i += 1
            continue

        raise SystemExit(f"Unknown argument: {arg}")

    return min_confidence, urls, write_mode

def should_promote(row: dict, min_confidence: int, chosen_urls: set[str]) -> bool:
    url = normalize_url(row.get("url", ""))
    confidence_raw = row.get("confidence", "") or "0"

    try:
        confidence = int(confidence_raw)
    except ValueError:
        confidence = 0

    if chosen_urls:
        return url in chosen_urls

    return confidence >= min_confidence

def main() -> None:
    min_confidence, chosen_urls, write_mode = parse_args(sys.argv[1:])

    canon_rows = load_csv(CANON)
    candidate_rows = load_csv(CANDIDATES)

    existing_keys = canon_keys(canon_rows)
    existing_urls = {normalize_url(r.get("url", "")) for r in canon_rows}

    promoted = []
    skipped = []

    for row in candidate_rows:
        if not should_promote(row, min_confidence, chosen_urls):
            continue

        normalized = normalize_candidate_row(row)
        key = (
            normalized["name"].strip().lower(),
            normalize_url(normalized["url"]),
        )
        norm_url = normalize_url(normalized["url"])

        if not norm_url:
            skipped.append((normalized["name"], normalized["url"], "blank normalized URL"))
            continue

        if key in existing_keys or norm_url in existing_urls:
            skipped.append((normalized["name"], normalized["url"], "already exists"))
            continue

        promoted.append(normalized)
        existing_keys.add(key)
        existing_urls.add(norm_url)

    merged = canon_rows + promoted

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CANON_FIELDS)
        writer.writeheader()
        writer.writerows(merged)

    print(f"Wrote preview: {OUTPUT}")
    print(f"Promoted: {len(promoted)}")
    print(f"Skipped: {len(skipped)}")

    if skipped:
        print("\nSkipped entries:")
        for name, url, reason in skipped[:25]:
            print(f"- {name} | {url} | {reason}")
        if len(skipped) > 25:
            print(f"... and {len(skipped) - 25} more")

    if write_mode:
        with open(CANON, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CANON_FIELDS)
            writer.writeheader()
            writer.writerows(merged)
        print(f"Updated canon in place: {CANON}")

if __name__ == "__main__":
    main()