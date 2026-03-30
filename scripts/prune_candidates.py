import csv, pathlib
from common import archive_fallback, soft_delete_target

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports" / "link-report.csv"
OUT = ROOT / "reports" / "prune-candidates.csv"

if not REPORT.exists():
    raise SystemExit("Run verify_links.py first.")

arch_cat, arch_sub = soft_delete_target()

with open(REPORT, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

candidates = []
for r in rows:
    if r["status"] in {"candidate_for_prune", "temporarily_down"}:
        c = dict(r)
        c["archive_fallback"] = archive_fallback(r["url"])
        c["soft_delete_category"] = arch_cat
        c["soft_delete_subcategory"] = arch_sub
        candidates.append(c)

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(
        f,
        fieldnames=["name","url","normalized_url","http_status","status","final_url","normalized_final_url","checked_at","error","archive_fallback","soft_delete_category","soft_delete_subcategory"]
    )
    writer.writeheader()
    writer.writerows(candidates)

print(f"Wrote {OUT}")
