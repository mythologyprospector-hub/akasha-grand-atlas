let atlas = [];
let filtered = [];

const searchInput = document.getElementById("search");
const categoryFilter = document.getElementById("categoryFilter");
const statusFilter = document.getElementById("statusFilter");
const freeFilter = document.getElementById("freeFilter");
const resultsEl = document.getElementById("results");
const totalCountEl = document.getElementById("totalCount");
const visibleCountEl = document.getElementById("visibleCount");

function safe(value) {
  return value == null ? "" : String(value);
}

function buildCategoryOptions(items) {
  const categories = [...new Set(items.map((x) => safe(x.category)).filter(Boolean))].sort();

  for (const cat of categories) {
    const opt = document.createElement("option");
    opt.value = cat;
    opt.textContent = cat;
    categoryFilter.appendChild(opt);
  }
}

function badgeText(item) {
  const badges = [];
  if (safe(item.free_tier) === "yes" || safe(item.free_tier) === "limited") {
    badges.push("free");
  }
  if (safe(item.catalog_or_supplier) === "yes") {
    badges.push("catalog");
  }
  return badges;
}

function render(items) {
  totalCountEl.textContent = String(atlas.length);
  visibleCountEl.textContent = String(items.length);

  if (!items.length) {
    resultsEl.innerHTML = `
      <div class="empty-state">
        No matches found. Try a broader query or loosen a filter.
      </div>
    `;
    return;
  }

  resultsEl.innerHTML = items.map((item) => {
    const badges = badgeText(item);
    const trust = safe(item.trust ?? item.trust_score ?? "?");
    const category = safe(item.category);
    const subcategory = safe(item.subcategory);
    const description = safe(item.description);
    const tags = safe(item.tags);
    const status = safe(item.status || "unknown");

    return `
      <article class="result-card">
        <h3>
          <a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.name}</a>
        </h3>
        <p class="result-desc">${description}</p>
        <p class="result-meta">${category}${subcategory ? " / " + subcategory : ""} · status ${status} · trust ${trust}</p>
        <p class="result-tags">${tags}</p>
        <p class="result-badges">${badges.join(" · ")}</p>
      </article>
    `;
  }).join("");
}

function applyFilters() {
  const q = safe(searchInput.value).trim().toLowerCase();
  const cat = safe(categoryFilter.value);
  const status = safe(statusFilter.value);
  const type = safe(freeFilter.value);

  filtered = atlas.filter((item) => {
    const searchable = safe(item.searchable).toLowerCase();
    const itemCategory = safe(item.category);
    const itemStatus = safe(item.status || "unknown");
    const badges = badgeText(item);

    const matchesQuery = !q || searchable.includes(q);
    const matchesCategory = !cat || itemCategory === cat;
    const matchesStatus = !status || itemStatus === status;
    const matchesType =
      !type ||
      (type === "free" && badges.includes("free")) ||
      (type === "catalog" && badges.includes("catalog"));

    return matchesQuery && matchesCategory && matchesStatus && matchesType;
  });

  filtered.sort((a, b) => {
    const ta = Number(a.trust ?? a.trust_score ?? 0);
    const tb = Number(b.trust ?? b.trust_score ?? 0);
    return tb - ta;
  });

  render(filtered);
}

fetch("../generated/search-index.json")
  .then((r) => r.json())
  .then((data) => {
    atlas = data;
    buildCategoryOptions(atlas);
    applyFilters();
  })
  .catch((err) => {
    console.error("Failed to load search index:", err);
    resultsEl.innerHTML = `
      <div class="empty-state">
        Failed to load <code>generated/search-index.json</code>. Run the build again:
        <pre>python scripts/build_atlas.py</pre>
      </div>
    `;
  });

searchInput.addEventListener("input", applyFilters);
categoryFilter.addEventListener("change", applyFilters);
statusFilter.addEventListener("change", applyFilters);
freeFilter.addEventListener("change", applyFilters);