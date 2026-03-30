import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "bookmarks.csv"
SUGGEST = ROOT / "reports" / "replacement-suggestions.csv"
OUT = ROOT / "reports" / "bookmarks.auto-fixed.csv"

if not SUGGEST.exists():
    raise SystemExit("Run suggest_replacements.py first.")

with open(DATA, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
with open(SUGGEST, newline="", encoding="utf-8") as f:
    suggestions = list(csv.DictReader(f))

safe_map = {}
for s in suggestions:
    if s["confidence"] == "high" and s["suggested_url"]:
        safe_map[s["original_url"]] = s["suggested_url"]

fixed = []
for r in rows:
    new_r = dict(r)
    if r["url"] in safe_map:
        new_r["notes"] = (new_r["notes"] + " | " if new_r["notes"] else "") + "auto-fixed high-confidence replacement"
        new_r["url"] = safe_map[r["url"]]
        new_r["replacement_url"] = ""
        new_r["status"] = "active"
    fixed.append(new_r)

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(fixed)

print(f"Wrote {OUT}")
