import csv
import json
import html
import pathlib
from collections import defaultdict, Counter
from common import normalize_url, trust_score

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "bookmarks.csv"
GEN = ROOT / "generated"
SITE = ROOT / "site"
REPORTS = ROOT / "reports"

GEN.mkdir(exist_ok=True)
SITE.mkdir(exist_ok=True)
REPORTS.mkdir(exist_ok=True)

with open(DATA, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

rows.sort(key=lambda r: (r["category"].lower(), r["subcategory"].lower(), r["name"].lower()))

search = []
for r in rows:
    search.append({
        "name": r["name"],
        "url": r["url"],
        "category": r["category"],
        "subcategory": r["subcategory"],
        "tags": r["tags"],
        "description": r["description"],
        "trust": trust_score(r["url"]),
        "free_tier": r.get("free_tier", ""),
        "catalog_or_supplier": r.get("catalog_or_supplier", ""),
        "status": r.get("status", "unknown"),
        "normalized_url": normalize_url(r["url"]),
        "searchable": " ".join([
            r["name"],
            r["category"],
            r["subcategory"],
            r["tags"],
            r["description"],
            r["url"],
        ]).lower(),
    })

(GEN / "search-index.json").write_text(
    json.dumps(search, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

category_counts = Counter(r["category"] for r in rows)
stats = {
    "total_bookmarks": len(rows),
    "categories": dict(category_counts),
    "free_yes_or_limited": sum(1 for r in rows if r.get("free_tier") in {"yes", "limited"}),
    "suppliers_or_catalogs": sum(1 for r in rows if r.get("catalog_or_supplier") == "yes"),
}
(GEN / "stats.json").write_text(
    json.dumps(stats, indent=2, ensure_ascii=False),
    encoding="utf-8",
)

# Chrome / Netscape bookmarks export
cats = defaultdict(list)
for r in rows:
    cats[r["category"]].append(r)

parts = [
    '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
    '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
    '<TITLE>Grand Atlas</TITLE>',
    '<H1>Grand Atlas</H1>',
    '<DL><p>',
]

for c in sorted(cats):
    parts.append(f"<DT><H3>{html.escape(c)}</H3>")
    parts.append("<DL><p>")
    for r in cats[c]:
        attrs = [
            f'data-tags="{html.escape(r.get("tags", ""))}"',
            f'data-description="{html.escape(r.get("description", ""))}"',
            f'data-free-tier="{html.escape(r.get("free_tier", ""))}"',
            f'data-status="{html.escape(r.get("status", "unknown"))}"',
            f'data-normalized-url="{html.escape(normalize_url(r["url"]))}"',
            f'data-trust-score="{trust_score(r["url"])}"',
        ]
        parts.append(
            f'<DT><A HREF="{html.escape(r["url"])}" {" ".join(attrs)}>{html.escape(r["name"])}</A>'
        )
    parts.append("</DL><p>")

parts.append("</DL><p>")
(GEN / "bookmarks.html").write_text("\n".join(parts), encoding="utf-8")

# Main site cards
cards = []
for r in rows:
    badges = []
    if r.get("free_tier") in {"yes", "limited"}:
        badges.append("free")
    if r.get("catalog_or_supplier") == "yes":
        badges.append("catalog")

    cards.append(f"""
    <article class="card"
        data-search="{html.escape((r['name'] + ' ' + r['category'] + ' ' + r['subcategory'] + ' ' + r['tags'] + ' ' + r['description']).lower())}"
        data-category="{html.escape(r['category'])}"
        data-status="{html.escape(r.get('status', 'unknown'))}">
      <h3><a href="{html.escape(r['url'])}" target="_blank" rel="noopener noreferrer">{html.escape(r['name'])}</a></h3>
      <p class="meta">{html.escape(r['category'])} / {html.escape(r['subcategory'])} · trust {trust_score(r['url'])}</p>
      <p>{html.escape(r['description'])}</p>
      <p class="tags">{html.escape(r['tags'])}</p>
      <p class="badges">{' · '.join(badges)}</p>
    </article>
    """)

cat_options = "".join(
    f'<option value="{html.escape(c)}">{html.escape(c)}</option>'
    for c in sorted(category_counts)
)

index_html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Grand Atlas</title>
<link rel="stylesheet" href="./styles.css">
<style>
#palette {{
  display: none;
  position: fixed;
  top: 12%;
  left: 50%;
  transform: translateX(-50%);
  width: min(720px, 92vw);
  max-height: 70vh;
  overflow-y: auto;
  background: #0e1116;
  border: 1px solid #30363d;
  border-radius: 14px;
  padding: 20px;
  z-index: 9999;
  box-shadow: 0 20px 60px rgba(0,0,0,.45);
}}

#palette-input {{
  width: 100%;
  padding: 12px 14px;
  margin-bottom: 14px;
  background: #161b22;
  color: #e6edf3;
  border: 1px solid #30363d;
  border-radius: 10px;
}}

.palette-result {{
  padding: 10px 4px;
  border-bottom: 1px solid #222b36;
}}

.palette-result:last-child {{
  border-bottom: none;
}}

.palette-result a {{
  color: #7cc7ff;
  text-decoration: none;
  font-weight: 600;
}}

.palette-result small {{
  display: block;
  color: #9da7b3;
  margin-top: 4px;
}}

.palette-hint {{
  color: #9da7b3;
  font-size: .92rem;
  margin-top: 8px;
}}
</style>
</head>
<body>
<header>
  <h1>Grand Atlas</h1>
  <p>A free-first bookmark atlas generated from CSV data.</p>

  <div class="toolbar">
    <input id="q" type="search" placeholder="Search your atlas...">
    <label><input id="freeOnly" type="checkbox"> free-first only</label>
    <select id="categoryFilter">
      <option value="">All categories</option>
      {cat_options}
    </select>
    <select id="statusFilter">
      <option value="">All statuses</option>
      <option value="unknown">unknown</option>
      <option value="active">active</option>
      <option value="redirected">redirected</option>
      <option value="temporarily_down">temporarily_down</option>
      <option value="candidate_for_prune">candidate_for_prune</option>
      <option value="archived">archived</option>
    </select>
  </div>

  <p class="links">
    <a href="../generated/bookmarks.html">Download Chrome bookmarks export</a>
    ·
    <a href="./explorer.html">Open Atlas Explorer</a>
    ·
    <span>Press <strong>Ctrl + K</strong> for Command Palette</span>
  </p>

  <p class="links">
    <a href="../reports/duplicates.csv">Duplicates</a>
    ·
    <a href="../reports/prune-candidates.csv">Prune report</a>
    ·
    <a href="../reports/replacement-suggestions.csv">Replacement suggestions</a>
  </p>
</header>

<main>
  <section class="stats">
    <div>Total bookmarks: <strong>{len(rows)}</strong></div>
    <div>Categories: <strong>{len(category_counts)}</strong></div>
    <div>Free-first: <strong>{stats["free_yes_or_limited"]}</strong></div>
    <div>Catalogs/suppliers: <strong>{stats["suppliers_or_catalogs"]}</strong></div>
  </section>

  <section id="cards" class="grid">
    {"".join(cards)}
  </section>
</main>

<div id="palette">
  <input id="palette-input" placeholder="Search Atlas">
  <div id="palette-results"></div>
  <div class="palette-hint">Press Esc to close.</div>
</div>

<script src="./app.js"></script>
<script src="./palette.js"></script>
</body>
</html>
"""

(SITE / "index.html").write_text(index_html, encoding="utf-8")
print(f"Wrote {SITE / 'index.html'}")
print(f"Wrote {GEN / 'bookmarks.html'}")
print(f"Wrote {GEN / 'search-index.json'}")