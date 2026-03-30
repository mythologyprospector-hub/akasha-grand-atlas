import csv
import html
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

RANKED = ROOT / "reports" / "harvest-candidates-ranked.csv"
OUT = ROOT / "site" / "review-ranked.html"


def main():
    if not RANKED.exists():
        raise SystemExit(f"Missing file: {RANKED}")

    with open(RANKED, newline="", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("rank_bucket") == "review"]

    cards = []
    for r in rows:
        name = html.escape(r.get("name", ""))
        url = html.escape(r.get("url", ""))
        desc = html.escape(r.get("description", ""))
        category = html.escape(r.get("category", ""))
        subcategory = html.escape(r.get("subcategory", ""))
        source = html.escape(r.get("source", ""))
        score = html.escape(r.get("rank_score", "0"))
        reasons = html.escape(r.get("rank_reasons", ""))
        tags = html.escape(r.get("tags", ""))

        cards.append(f"""
        <div class="card" data-url="{url}" data-score="{score}">
          <h3><a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a></h3>
          <p class="desc">{desc}</p>

          <div class="meta">
            <span>category: {category}</span>
            <span>subcategory: {subcategory}</span>
            <span>rank: {score}</span>
          </div>

          <div class="meta">
            <span>tags: {tags}</span>
            <span>source: {source}</span>
          </div>

          <div class="reasons">{reasons}</div>

          <div class="actions">
            <button onclick="approve('{url}', this)">Approve</button>
            <button onclick="rejectCard(this)">Reject</button>
          </div>
        </div>
        """)

    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Atlas Ranked Review</title>
<style>
:root {{
  color-scheme: dark;
  --bg: #111;
  --panel: #1b1b1b;
  --panel2: #1f1f1f;
  --text: #eee;
  --muted: #aaa;
  --border: #2f2f2f;
  --link: #7cc7ff;
}}

* {{
  box-sizing: border-box;
}}

html {{
  scroll-behavior: smooth;
}}

body {{
  font-family: system-ui, sans-serif;
  background: var(--bg);
  color: var(--text);
  margin: 0;
  padding: 18px;
}}

.toolbar {{
  position: sticky;
  top: 0;
  z-index: 999;
  background: rgba(17, 17, 17, 0.97);
  border-bottom: 1px solid var(--border);
  padding: 14px 0 16px;
  margin-bottom: 20px;
  backdrop-filter: blur(8px);
}}

.toolbar h1 {{
  margin: 0 0 8px 0;
  font-size: 1.5rem;
}}

.toolbar-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-top: 10px;
}}

.counts {{
  color: var(--muted);
  font-size: 14px;
}}

button {{
  padding: 9px 12px;
  border-radius: 8px;
  border: 1px solid #333;
  background: #222;
  color: var(--text);
  cursor: pointer;
}}

button:hover {{
  background: #2a2a2a;
}}

button:disabled {{
  opacity: 0.6;
  cursor: default;
}}

.card {{
  background: var(--panel);
  padding: 18px;
  margin-bottom: 14px;
  border-radius: 12px;
  border: 1px solid var(--border);
}}

.card h3 {{
  margin: 0 0 8px 0;
  line-height: 1.3;
}}

.card a {{
  color: var(--link);
  text-decoration: none;
}}

.card a:hover {{
  text-decoration: underline;
}}

.desc {{
  margin: 0 0 10px 0;
}}

.meta {{
  font-size: 12px;
  color: var(--muted);
  margin: 6px 0;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}}

.reasons {{
  margin-top: 10px;
  font-size: 12px;
  color: #c7c7c7;
  background: var(--panel2);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 10px;
}}

.actions {{
  margin-top: 14px;
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}}

.footer-tools {{
  margin-top: 24px;
  padding: 16px 0 40px;
}}

.spacer {{
  flex: 1 1 auto;
}}

.note {{
  color: var(--muted);
  font-size: 13px;
}}

@media (max-width: 700px) {{
  body {{
    padding: 12px;
  }}

  .toolbar h1 {{
    font-size: 1.25rem;
  }}

  button {{
    width: 100%;
  }}

  .actions button,
  .toolbar-row button {{
    width: auto;
  }}
}}
</style>
</head>
<body>

<div class="toolbar" id="top">
  <h1>Atlas Ranked Review Queue</h1>

  <div class="counts">
    <span id="visibleCount">Visible: 0</span> ·
    <span id="approvedCount">Approved: 0</span>
  </div>

  <div class="toolbar-row">
    <button onclick="exportApproved()">Save Approved List</button>
    <button onclick="window.scrollTo({{ top: 0, behavior: 'smooth' }})">Go to Top</button>
    <button onclick="window.scrollTo({{ top: document.body.scrollHeight, behavior: 'smooth' }})">Go to Bottom</button>
    <div class="spacer"></div>
    <span class="note">Only items in the <strong>review</strong> bucket are shown here.</span>
  </div>
</div>

<div id="cards">
{''.join(cards) if cards else '<p>No review items.</p>'}
</div>

<div class="footer-tools">
  <button onclick="exportApproved()">Save Approved List</button>
  <button onclick="window.scrollTo({{ top: 0, behavior: 'smooth' }})">Go to Top</button>
</div>

<script>
let approved = [];

function updateCounts() {{
  const visible = document.querySelectorAll(".card").length;
  document.getElementById("visibleCount").textContent = "Visible: " + visible;
  document.getElementById("approvedCount").textContent = "Approved: " + approved.length;
}}

function approve(url, btn) {{
  if (!approved.includes(url)) {{
    approved.push(url);
  }}
  btn.textContent = "Approved";
  btn.disabled = true;
  updateCounts();
}}

function rejectCard(btn) {{
  const card = btn.closest(".card");
  if (card) {{
    card.remove();
    updateCounts();
  }}
}}

function exportApproved() {{
  let csv = "url\\n";
  approved.forEach(u => {{
    csv += u + "\\n";
  }});

  const blob = new Blob([csv], {{ type: "text/csv" }});
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "approved-ranked-candidates.csv";
  a.click();
}}

updateCounts();
</script>

</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Review items: {len(rows)}")


if __name__ == "__main__":
    main()