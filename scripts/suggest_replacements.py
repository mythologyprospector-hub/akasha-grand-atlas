import csv, pathlib
from urllib.parse import urlparse
from common import normalize_url, KNOWN_REPLACEMENTS, archive_fallback, category_matches, trust_score

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "link-report.csv"
DATA = ROOT / "data" / "bookmarks.csv"
OUT = ROOT / "reports" / "replacement-suggestions.csv"

if not REPORT.exists():
    raise SystemExit("Run verify_links.py first.")

with open(REPORT, newline="", encoding="utf-8") as f:
    reports = list(csv.DictReader(f))
with open(DATA, newline="", encoding="utf-8") as f:
    rows = {r["url"]: r for r in csv.DictReader(f)}

def guess_replacement(url: str, final_url: str, status: str, category: str):
    nu = normalize_url(url)
    nf = normalize_url(final_url or "")
    if nf and nf != nu and status == "redirected" and category_matches(category, nf):
        return nf, "use final redirected URL", "high"
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    key1 = host
    key2 = (host + parsed.path).lower()
    if key2 in KNOWN_REPLACEMENTS and category_matches(category, KNOWN_REPLACEMENTS[key2]):
        return KNOWN_REPLACEMENTS[key2], "known replacement map", "medium"
    if key1 in KNOWN_REPLACEMENTS and category_matches(category, KNOWN_REPLACEMENTS[key1]):
        return KNOWN_REPLACEMENTS[key1], "known replacement map", "medium"
    if host.startswith("www."):
        candidate = f"{parsed.scheme}://{host[4:]}{parsed.path or ''}"
        return candidate, "try non-www variant", "low"
    if host and not host.startswith("www."):
        candidate = f"{parsed.scheme}://www.{host}{parsed.path or ''}"
        return candidate, "try www variant", "low"
    return "", "", "low"

suggestions = []
for rep in reports:
    if rep["status"] not in {"redirected", "candidate_for_prune", "temporarily_down"}:
        continue
    row = rows.get(rep["url"], {})
    suggested_url, reason, confidence = guess_replacement(rep["url"], rep["final_url"], rep["status"], row.get("category", ""))
    suggestions.append({
        "name": rep["name"],
        "original_url": rep["url"],
        "status": rep["status"],
        "http_status": rep["http_status"],
        "final_url": rep["final_url"],
        "suggested_url": suggested_url,
        "reason": reason,
        "confidence": confidence,
        "archive_fallback": archive_fallback(rep["url"]),
        "category": row.get("category", ""),
        "subcategory": row.get("subcategory", ""),
        "suggested_trust": trust_score(suggested_url) if suggested_url else "",
    })

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=[
            "name","original_url","status","http_status","final_url",
            "suggested_url","reason","confidence","archive_fallback","category","subcategory","suggested_trust"
        ]
    )
    writer.writeheader()
    writer.writerows(suggestions)

print(f"Wrote {OUT}")
