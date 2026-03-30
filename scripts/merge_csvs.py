import csv,sys,pathlib
from common import normalize_url

files=sys.argv[1:]
rows=[]
seen=set()

for f in files:
    for r in csv.DictReader(open(f)):
        key=(r["name"].lower(),normalize_url(r["url"]))
        if key not in seen:
            seen.add(key)
            rows.append(r)

out=pathlib.Path("reports/merged.csv")
out.parent.mkdir(exist_ok=True)

with open(out,"w",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys())
    w.writeheader()
    w.writerows(rows)

print("merged ->",out)
