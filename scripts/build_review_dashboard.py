import csv
import html
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]

CANDIDATES = ROOT / "reports" / "harvest-candidates-v3.csv"
OUT = ROOT / "site" / "review.html"


def load_candidates():
    if not CANDIDATES.exists():
        return []

    with open(CANDIDATES, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def build():
    rows = load_candidates()

    cards = []

    for r in rows:
        name = html.escape(r.get("name", ""))
        url = html.escape(r.get("url", ""))
        desc = html.escape(r.get("description", ""))
        category = html.escape(r.get("category", ""))
        subcategory = html.escape(r.get("subcategory", ""))
        source = html.escape(r.get("source", ""))
        confidence = html.escape(r.get("confidence", "0"))
        tags = html.escape(r.get("tags", ""))

        cards.append(f"""
        <div class="card" data-url="{url}">
            <h3><a href="{url}" target="_blank" rel="noopener noreferrer">{name}</a></h3>
            <p>{desc}</p>

            <div class="meta">
                <span>category: {category}</span>
                <span>subcategory: {subcategory}</span>
                <span>confidence: {confidence}</span>
            </div>

            <div class="meta">
                <span>tags: {tags}</span>
                <span>source: {source}</span>
            </div>

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
<title>Atlas Candidate Review</title>
<style>
body {{
  font-family: system-ui, sans-serif;
  background: #111;
  color: #eee;
  padding: 24px;
  margin: 0;
}}

.toolbar {{
  position: sticky;
  top: 0;
  z-index: 999;
  background: rgba(17, 17, 17, 0.97);
  border-bottom: 1px solid #2a2a2a;
  padding: 14px 0 16px;
  margin-bottom: 20px;
}}

.toolbar-row {{
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  margin-top: 10px;
}}

.card {{
  background: #1b1b1b;
  padding: 20px;
  margin-bottom: 16px;
  border-radius: 10px;
  border: 1px solid #2a2a2a;
}}

.meta {{
  font-size: 12px;
  color: #aaa;
  margin: 8px 0;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}}

button {{
  margin-right: 10px;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #333;
  background: #222;
  color: #eee;
  cursor: pointer;
}}

button:hover {{
  background: #2a2a2a;
}}

a {{
  color: #7cc7ff;
}}

.counts {{
  color: #aaa;
  font-size: 14px;
}}

.footer-tools {{
  margin-top: 28px;
  padding: 16px 0 40px;
}}

.spacer {{
  flex: 1 1 auto;
}}
</style>
</head>
<body>

<div class="toolbar">
  <h1>Atlas Candidate Review</h1>
  <div class="counts">
    <span id="candidateCount"></span> ·
    <span id="approvedCount">Approved: 0</span>
  </div>

  <div class="toolbar-row">
    <button onclick="exportApproved()">Save Approved List</button>
    <button onclick="window.scrollTo({{ top: 0, behavior: 'smooth' }})">Go to Top</button>
    <button onclick="window.scrollTo({{ top: document.body.scrollHeight, behavior: 'smooth' }})">Go to Bottom</button>
    <div class="spacer"></div>
    <span style="color:#aaa;">Approved downloads as <code>approved-candidates.csv</code></span>
  </div>
</div>

<div id="cards">
{''.join(cards) if cards else '<p>No candidates found.</p>'}
</div>

<div class="footer-tools">
  <button onclick="exportApproved()">Save Approved List</button>
  <button onclick="window.scrollTo({{ top: 0, behavior: 'smooth' }})">Go to Top</button>
</div>

<script>
let approved = [];

function updateCounts() {{
  const cardCount = document.querySelectorAll(".card").length;
  document.getElementById("candidateCount").textContent = "Candidates visible: " + cardCount;
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
  a.download = "approved-candidates.csv";
  a.click();
}}

updateCounts();
</script>

</body>
</html>
"""
    OUT.write_text(page, encoding="utf-8")
    print(f"dashboard written: {OUT}")


if __name__ == "__main__":
    build()