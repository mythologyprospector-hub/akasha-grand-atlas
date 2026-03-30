import csv
import os
import pathlib
import re
import time
from urllib.parse import urlparse

import requests

from common import normalize_url

ROOT = pathlib.Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "bookmarks.csv"
REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

OUTPUT = REPORTS / "harvest-candidates-v3.csv"

RAW_SOURCES = [
    "https://raw.githubusercontent.com/sindresorhus/awesome/main/readme.md",
    "https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md",
    "https://raw.githubusercontent.com/jivoi/awesome-osint/master/README.md",
    "https://raw.githubusercontent.com/sbilly/awesome-security/master/README.md",
    "https://raw.githubusercontent.com/datasets/awesome-data/master/README.md",
    "https://raw.githubusercontent.com/public-apis/public-apis/master/README.md",
]

GITHUB_TOPIC_QUERIES = [
    "awesome tool",
    "awesome utility",
    "awesome dataset",
    "awesome osint",
    "awesome cybersecurity",
    "free developer tools",
    "fdroid android app",
]

URL_PATTERN = re.compile(r"\[(.*?)\]\((https?://.*?)\)")

CATEGORY_HINTS = {
    "ai": "AI",
    "machine learning": "AI",
    "llm": "AI",
    "model": "AI",
    "dataset": "Datasets",
    "data": "Datasets",
    "security": "Security",
    "cybersecurity": "Security",
    "osint": "Security",
    "forensics": "Security",
    "android": "Android",
    "apk": "Android",
    "fdroid": "Android",
    "tool": "Web Tools",
    "utility": "Web Tools",
    "converter": "Web Tools",
    "pdf": "Web Tools",
    "archive": "Archives",
    "library": "Archives",
    "education": "Education",
    "course": "Education",
    "textbook": "Education",
    "chem": "Datasets",
    "biology": "Datasets",
    "science": "Datasets",
    "mycology": "Mycology",
    "fungi": "Mycology",
    "hardware": "Materials",
    "supplier": "Materials",
    "electronics": "Materials",
    "api": "Web Tools",
}

SUBCATEGORY_HINTS = {
    "osint": "OSINT",
    "cybersecurity": "Security",
    "forensics": "DFIR",
    "dataset": "Data",
    "android": "Apps",
    "fdroid": "Apps",
    "converter": "Conversion",
    "pdf": "PDF",
    "education": "Courses",
    "textbook": "Textbooks",
    "archive": "Archive",
    "library": "Library",
    "fungi": "Observation",
    "mycology": "Observation",
    "hardware": "Supplier",
    "electronics": "Supplier",
    "api": "API",
}

BAD_HOST_FRAGMENTS = {
    "img.shields.io",
    "github.com/sponsors",
    "opencollective.com",
    "travis-ci.org",
    "travis-ci.com",
    "coveralls.io",
    "codecov.io",
}

BAD_NAME_EXACT = {
    "license",
    "build status",
    "coverage",
    "sponsor",
    "donate",
}

HACKERNEWS_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HACKERNEWS_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
FDROID_INDEX_URL = "https://f-droid.org/repo/index-v2.json"


def safe_text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # common localized-object shapes
        for key in ("en-US", "en", "name", "summary", "description", "value"):
            inner = value.get(key)
            if isinstance(inner, str):
                return inner
        return ""
    if isinstance(value, list):
        for item in value:
            text = safe_text(item)
            if text:
                return text
        return ""
    return str(value)


def load_existing_urls() -> set[str]:
    existing = set()

    if not DATA.exists():
        return existing

    with open(DATA, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = safe_text(row.get("url", "")).strip()
            if url:
                existing.add(normalize_url(url))

    return existing


def looks_like_junk_name(name) -> bool:
    stripped = safe_text(name).strip()
    lowered = stripped.lower()

    if not stripped:
        return True

    if stripped.startswith("!"):
        return True
    if stripped.startswith("[!"):
        return True
    if lowered in BAD_NAME_EXACT:
        return True
    if len(stripped) < 4:
        return True

    return False


def extract_markdown_links(text: str) -> list[tuple[str, str]]:
    links = []

    for name, url in URL_PATTERN.findall(text):
        name = safe_text(name).strip()
        url = safe_text(url).strip()

        if not url.startswith("https://"):
            continue

        if looks_like_junk_name(name):
            continue

        parsed = urlparse(url)
        host = parsed.netloc.lower()

        if any(fragment in host or fragment in url for fragment in BAD_HOST_FRAGMENTS):
            continue

        links.append((name, url))

    return links


def infer_category(text: str) -> str:
    lowered = safe_text(text).lower()

    for hint, category in CATEGORY_HINTS.items():
        if hint in lowered:
            return category

    return "candidate"


def infer_subcategory(text: str) -> str:
    lowered = safe_text(text).lower()

    for hint, subcategory in SUBCATEGORY_HINTS.items():
        if hint in lowered:
            return subcategory

    return "harvested"


def generate_tags(name: str, url: str, source: str) -> str:
    tags: list[str] = []

    host = urlparse(url).netloc.lower()
    source_lower = source.lower()
    name_lower = name.lower()

    if "github.com" in host:
        tags.append("github")
    if "gitlab.com" in host:
        tags.append("gitlab")
    if "f-droid.org" in host:
        tags.append("fdroid")
    if "ycombinator.com" in host or "hackernews" in source_lower:
        tags.append("hackernews")

    for hint in CATEGORY_HINTS:
        if hint in name_lower:
            tags.append(hint.replace(" ", "_"))

    if "awesome" in source_lower:
        tags.append("awesome_list")
    if "github api" in source_lower:
        tags.append("github_api")
    if "fdroid catalog" in source_lower:
        tags.append("fdroid_catalog")

    deduped = []
    seen = set()
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            deduped.append(tag)

    return ",".join(deduped)


def confidence_score(name: str, url: str, source: str) -> int:
    score = 40

    host = urlparse(url).netloc.lower()
    source_lower = source.lower()
    name_lower = name.lower()

    if "awesome" in source_lower:
        score += 20
    if "github api" in source_lower:
        score += 10
    if "fdroid catalog" in source_lower:
        score += 16
    if "hackernews" in source_lower:
        score += 8
    if "github.com" in host:
        score += 8
    if "f-droid.org" in host:
        score += 14
    if any(k in name_lower for k in ("awesome", "tool", "dataset", "security", "android", "library", "api")):
        score += 10
    if len(name.strip()) > 3:
        score += 5
    if looks_like_junk_name(name):
        score -= 25

    return max(0, min(score, 95))


def add_candidate(
    candidates: dict[str, dict],
    existing: set[str],
    name,
    url,
    source: str,
) -> None:
    name = safe_text(name).strip()
    url = safe_text(url).strip()

    if looks_like_junk_name(name):
        return

    norm = normalize_url(url)

    if not norm or norm in existing or norm in candidates:
        return

    category = infer_category(f"{name} {url} {source}")
    subcategory = infer_subcategory(f"{name} {url} {source}")
    tags = generate_tags(name, url, source)
    confidence = confidence_score(name, url, source)

    candidates[norm] = {
        "name": name[:160].strip(),
        "url": url.strip(),
        "category": category,
        "subcategory": subcategory,
        "tags": tags,
        "description": "discovered by atlas harvester",
        "free_tier": "",
        "catalog_or_supplier": "",
        "status": "unknown",
        "last_checked": "",
        "replacement_url": "",
        "notes": "",
        "source": source,
        "confidence": str(confidence),
    }


def harvest_raw_sources(candidates: dict[str, dict], existing: set[str]) -> None:
    session = requests.Session()
    session.headers.update({"User-Agent": "GrandAtlasHarvester/0.5"})

    for src in RAW_SOURCES:
        print("fetching raw source:", src)
        try:
            response = session.get(src, timeout=25)
            response.raise_for_status()
        except Exception as exc:
            print("failed:", src, "-", exc)
            continue

        for name, url in extract_markdown_links(response.text):
            add_candidate(
                candidates=candidates,
                existing=existing,
                name=name,
                url=url,
                source=f"raw markdown: {src}",
            )


def github_api_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "GrandAtlasHarvester/0.5",
    }
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def harvest_github_api(candidates: dict[str, dict], existing: set[str]) -> None:
    headers = github_api_headers()
    session = requests.Session()
    session.headers.update(headers)

    for query in GITHUB_TOPIC_QUERIES:
        print("fetching github api query:", query)

        url = "https://api.github.com/search/repositories"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": 25,
        }

        try:
            response = session.get(url, params=params, timeout=25)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            print("failed github query:", query, "-", exc)
            continue

        items = payload.get("items", [])

        for item in items:
            full_name = safe_text(item.get("full_name", "")).strip()
            html_url = safe_text(item.get("html_url", "")).strip()
            description = safe_text(item.get("description", "")).strip()
            topics = item.get("topics", []) or []

            if not full_name or not html_url:
                continue

            add_candidate(
                candidates=candidates,
                existing=existing,
                name=full_name,
                url=html_url,
                source=f"github api: {query}",
            )

            norm = normalize_url(html_url)
            if norm in candidates:
                extra_tags = candidates[norm]["tags"].split(",") if candidates[norm]["tags"] else []
                for topic in topics[:8]:
                    topic = safe_text(topic).strip().replace(" ", "_")
                    if topic and topic not in extra_tags:
                        extra_tags.append(topic)

                candidates[norm]["tags"] = ",".join([t for t in extra_tags if t])

                if description:
                    candidates[norm]["description"] = description[:240]

        time.sleep(1.2)


def _pick_fdroid_package_data(package_key: str, value):
    package_name = safe_text(package_key).strip()
    suggested_name = package_name
    summary = ""

    if isinstance(value, dict):
        metadata = value.get("metadata") or {}
        package_name = safe_text(
            metadata.get("packageName")
            or metadata.get("package_name")
            or package_key
        ).strip()

        suggested_name = safe_text(
            metadata.get("name")
            or metadata.get("localizedName")
            or metadata.get("summary")
            or package_name
        ).strip()

        summary = safe_text(
            metadata.get("summary")
            or metadata.get("description")
            or ""
        ).strip()

    return package_name, suggested_name, summary


def harvest_fdroid_catalog(candidates: dict[str, dict], existing: set[str]) -> None:
    print("fetching F-Droid catalog")

    session = requests.Session()
    session.headers.update({"User-Agent": "GrandAtlasHarvester/0.5"})

    try:
        response = session.get(FDROID_INDEX_URL, timeout=40)
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        print("fdroid harvest failed:", exc)
        return

    packages = payload.get("packages", {})
    if not isinstance(packages, dict):
        print("fdroid harvest failed: unexpected packages shape")
        return

    count = 0

    for package_key, package_value in packages.items():
        if count >= 500:
            break

        try:
            package_name, suggested_name, summary = _pick_fdroid_package_data(package_key, package_value)
        except Exception:
            continue

        if not package_name:
            continue

        link = f"https://f-droid.org/packages/{package_name}/"

        add_candidate(
            candidates=candidates,
            existing=existing,
            name=suggested_name or package_name,
            url=link,
            source="fdroid catalog",
        )

        norm = normalize_url(link)
        if norm in candidates:
            if summary:
                candidates[norm]["description"] = summary[:240]

            extra = candidates[norm]["tags"].split(",") if candidates[norm]["tags"] else []
            for tag in ("android", "fdroid"):
                if tag not in extra:
                    extra.append(tag)
            candidates[norm]["tags"] = ",".join([t for t in extra if t])

        count += 1


def harvest_hackernews(candidates: dict[str, dict], existing: set[str]) -> None:
    print("fetching hackernews")

    session = requests.Session()
    session.headers.update({"User-Agent": "GrandAtlasHarvester/0.5"})

    try:
        story_ids = session.get(HACKERNEWS_TOP_URL, timeout=20).json()
    except Exception as exc:
        print("hn fetch failed:", exc)
        return

    for story_id in story_ids[:120]:
        try:
            item = session.get(HACKERNEWS_ITEM_URL.format(story_id=story_id), timeout=20).json()
        except Exception:
            continue

        if not item:
            continue

        title = safe_text(item.get("title", "")).strip()
        url = safe_text(item.get("url", "")).strip()

        if not title or not url:
            continue

        add_candidate(
            candidates=candidates,
            existing=existing,
            name=title,
            url=url,
            source="hackernews",
        )


def write_output(candidates: dict[str, dict]) -> None:
    fieldnames = [
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
        "source",
        "confidence",
    ]

    sorted_rows = sorted(
        candidates.values(),
        key=lambda r: (
            r["category"].lower(),
            -int(r["confidence"]),
            r["name"].lower(),
        ),
    )

    with open(OUTPUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted_rows)

    print("wrote", OUTPUT)
    print("candidate count:", len(sorted_rows))


def main() -> None:
    existing = load_existing_urls()
    candidates: dict[str, dict] = {}

    harvest_raw_sources(candidates, existing)
    harvest_github_api(candidates, existing)
    harvest_fdroid_catalog(candidates, existing)
    harvest_hackernews(candidates, existing)
    write_output(candidates)


if __name__ == "__main__":
    main()