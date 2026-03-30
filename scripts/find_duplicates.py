import csv,pathlib
from collections import defaultdict
from common import normalize_url

ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"bookmarks.csv"
OUT=ROOT/"reports"/"duplicates.csv"
OUT.parent.mkdir(exist_ok=True)

rows=list(csv.DictReader(open(DATA)))

dupes=[]
seen=defaultdict(list)
for r in rows:
    seen[normalize_url(r["url"])].append(r)

for k,v in seen.items():
    if len(v)>1:
        for r in v:
            dupes.append(r)

with open(OUT,"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(dupes)
print("wrote",OUT)
