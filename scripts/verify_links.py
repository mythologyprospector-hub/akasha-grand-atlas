import csv, requests, pathlib, datetime
from common import normalize_url

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "bookmarks.csv"
OUT = ROOT / "reports" / "link-report.csv"
OUT.parent.mkdir(exist_ok=True)

rows = list(csv.DictReader(open(DATA)))

results = []
for r in rows:
    try:
        resp = requests.get(r["url"], timeout=8)
        status = "active" if resp.status_code < 400 else "candidate_for_prune"
    except:
        status = "temporarily_down"

    results.append({
        "name": r["name"],
        "url": r["url"],
        "status": status,
        "checked": datetime.datetime.now(datetime.UTC).isoformat()
    })

with open(OUT, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["name", "url", "status", "checked"])
    w.writeheader()
    w.writerows(results)

print("wrote", OUT)