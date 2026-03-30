import csv, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "bookmarks.csv"
SUGGEST = ROOT / "reports" / "replacement-suggestions.csv"
OUT = ROOT / "reports" / "bookmarks.patched.preview.csv"

if not SUGGEST.exists():
    raise SystemExit("Run suggest_replacements.py first.")

with open(DATA, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))
with open(SUGGEST, newline="", encoding="utf-8") as f:
    suggestions = list(csv.DictReader(f))

best = {}
for s in suggestions:
    if s["suggested_url"] and s["confidence"] in {"high", "medium"}:
        best[s["original_url"]] = s["suggested_url"]

patched = []
for r in rows:
    new_r = dict(r)
    if r["url"] in best:
        new_r["replacement_url"] = best[r["url"]]
        if new_r["status"] == "unknown":
            new_r["status"] = "replaced"
        new_r["notes"] = (new_r["notes"] + " | " if new_r["notes"] else "") + "suggested replacement available"
    patched.append(new_r)

with open(OUT, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(patched)

print(f"Wrote {OUT}")
