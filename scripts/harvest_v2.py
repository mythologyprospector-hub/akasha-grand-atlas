import csv
import pathlib
import re
import requests
from urllib.parse import urlparse
from common import normalize_url

ROOT = pathlib.Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "bookmarks.csv"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

OUTPUT = REPORTS / "harvest-candidates-v2.csv"

# curated sources
SOURCES = [
    "https://raw.githubusercontent.com/sindresorhus/awesome/main/readme.md",
    "https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md",
    "https://raw.githubusercontent.com/jivoi/awesome-osint/master/README.md",
    "https://raw.githubusercontent.com/opsxcq/awesome-cybersecurity/master/README.md",
    "https://raw.githubusercontent.com/datasets/awesome-data/master/README.md",
]

URL_PATTERN = re.compile(r"\[(.*?)\]\((https?://.*?)\)")

CATEGORY_HINTS = {
    "ai": "AI",
    "machine learning": "AI",
    "dataset": "Datasets",
    "data": "Datasets",
    "security": "Security",
    "osint": "Security",
    "android": "Android",
    "tool": "Web Tools",
    "converter": "Web Tools",
    "archive": "Archives",
    "education": "Education",
    "course": "Education",
}

def load_existing():

    existing = set()

    with open(DATA, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for r in reader:
            existing.add(normalize_url(r["url"]))

    return existing


def infer_category(text):

    text = text.lower()

    for key, value in CATEGORY_HINTS.items():
        if key in text:
            return value

    return "candidate"


def extract_links(text):

    links = []

    for match in URL_PATTERN.findall(text):

        name, url = match

        if url.startswith("https://"):
            links.append((name.strip(), url.strip()))

    return links


def generate_tags(name, url):

    tags = []

    parsed = urlparse(url)

    if "github.com" in parsed.netloc:
        tags.append("github")

    name_lower = name.lower()

    for key in CATEGORY_HINTS:
        if key in name_lower:
            tags.append(key)

    return ",".join(tags)


def harvest():

    existing = load_existing()

    candidates = {}

    for src in SOURCES:

        print("fetching", src)

        try:
            r = requests.get(src, timeout=20)
            text = r.text
        except:
            print("failed:", src)
            continue

        links = extract_links(text)

        for name, url in links:

            norm = normalize_url(url)

            if norm in existing:
                continue

            if norm in candidates:
                continue

            category = infer_category(name)

            tags = generate_tags(name, url)

            candidates[norm] = {
                "name": name[:120],
                "url": url,
                "category": category,
                "subcategory": "harvested",
                "tags": tags,
                "description": "discovered by atlas harvester",
                "free_tier": "",
                "catalog_or_supplier": "",
                "status": "unknown",
                "last_checked": "",
                "replacement_url": "",
                "notes": "",
            }

    print("candidates discovered:", len(candidates))

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
        writer.writerows(candidates.values())

    print("wrote", OUTPUT)


if __name__ == "__main__":
    harvest()