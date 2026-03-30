let atlas = [];
let paletteOpen = false;

fetch("../generated/search-index.json")
  .then((r) => r.json())
  .then((d) => {
    atlas = d;
  })
  .catch((err) => {
    console.error("Failed to load atlas index:", err);
  });

function openPalette() {
  const palette = document.getElementById("palette");
  const input = document.getElementById("palette-input");
  if (!palette || !input) return;

  palette.style.display = "block";
  input.focus();
  input.select();
  paletteOpen = true;
}

function closePalette() {
  const palette = document.getElementById("palette");
  const input = document.getElementById("palette-input");
  const results = document.getElementById("palette-results");

  if (!palette || !input || !results) return;

  palette.style.display = "none";
  input.value = "";
  results.innerHTML = "";
  paletteOpen = false;
}

function renderPaletteResults(results) {
  const target = document.getElementById("palette-results");
  if (!target) return;

  if (!results.length) {
    target.innerHTML = `<div class="palette-result"><small>No matches found.</small></div>`;
    return;
  }

  let out = "";

  for (const r of results) {
    out += `
      <div class="palette-result">
        <a href="${r.url}" target="_blank" rel="noopener noreferrer">${r.name}</a>
        <small>${r.category}${r.subcategory ? " / " + r.subcategory : ""} · trust ${r.trust ?? "?"}</small>
      </div>
    `;
  }

  target.innerHTML = out;
}

function searchAtlas(query) {
  const q = query.trim().toLowerCase();

  if (!q) {
    renderPaletteResults([]);
    return;
  }

  const results = atlas
    .filter((x) => (x.searchable || "").includes(q))
    .sort((a, b) => (b.trust ?? 0) - (a.trust ?? 0))
    .slice(0, 20);

  renderPaletteResults(results);
}

document.addEventListener("keydown", (e) => {
  if (e.ctrlKey && e.key.toLowerCase() === "k") {
    e.preventDefault();
    if (paletteOpen) closePalette();
    else openPalette();
  }

  if (e.key === "Escape" && paletteOpen) {
    closePalette();
  }
});

document.addEventListener("input", (e) => {
  if (e.target && e.target.id === "palette-input") {
    searchAtlas(e.target.value);
  }
});