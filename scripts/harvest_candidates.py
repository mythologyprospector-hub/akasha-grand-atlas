import csv
import json
import pathlib
import re
import requests
from common import normalize_url

ROOT = pathlib.Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "bookmarks.csv"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

OUTPUT = REPORTS / "harvest-candidates.csv"

# Curated sources
SOURCES = [
    "https://raw.githubusercontent.com/sindresorhus/awesome/main/readme.md",
    "https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md",
    "https://raw.githubusercontent.com/opsxcq/awesome-cybersecurity/master/README.md",
    "https://raw.githubusercontent.com/jivoi/awesome-osint/master/README.md",
]

URL_PATTERN = re.compile(r"\[(.*?)\]\((https?://.*?)\)")

def load_existing():
    existing = set()

    with open(DATA, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            existing.add(normalize_url(r["url"]))

    return existing


def extract_links(text):
    links = []

    for match in URL_PATTERN.findall(text):
        name, url = match
        if url.startswith("https://"):
            links.append((name.strip(), url.strip()))

    return links


def harvest():

    existing = load_existing()
    candidates = []

    for src in SOURCES:

        try:
            print("fetching", src)
            r = requests.get(src, timeout=20)
            text = r.text
        except Exception as e:
            print("failed:", src)
            continue

        links = extract_links(text)

        for name, url in links:

            norm = normalize_url(url)

            if norm in existing:
                continue

            candidates.append({
                "name": name[:120],
                "url": url,
                "category": "candidate",
                "subcategory": "harvested",
                "tags": "harvest",
                "description": "discovered by atlas harvester",
                "free_tier": "",
                "catalog_or_supplier": "",
                "status": "unknown",
                "last_checked": "",
                "replacement_url": "",
                "notes": ""
            })

    print("found", len(candidates), "candidates")

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "name",
                "url",
                "category",
                "subcategory",
                "tags",
                "description",
                "free_tier",
                "catalog_or_supplier",
                "status",
                "last_checked",
                "replacement_url",
                "notes",
            ],
        )

        writer.writeheader()
        writer.writerows(candidates)

    print("wrote", OUTPUT)


if __name__ == "__main__":
    harvest()