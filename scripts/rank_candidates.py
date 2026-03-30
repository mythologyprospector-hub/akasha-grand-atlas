import csv
import pathlib
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]

INFILE = ROOT / "reports" / "harvest-candidates-v3.csv"
OUTFILE = ROOT / "reports" / "harvest-candidates-ranked.csv"

GOOD_DOMAINS = {
    "github.com": 18,
    "gitlab.com": 14,
    "huggingface.co": 18,
    "arxiv.org": 16,
    "pypi.org": 14,
    "npmjs.com": 14,
    "crates.io": 14,
    "developer.android.com": 18,
    "source.android.com": 18,
    "data.gov": 18,
    "archive.org": 16,
    "openstax.org": 16,
    "ocw.mit.edu": 18,
    "khanacademy.org": 16,
    "f-droid.org": 18,
    "news.ycombinator.com": 8,
}

GOOD_TAGS = {
    "github": 8,
    "awesome_list": 8,
    "android": 8,
    "security": 8,
    "dataset": 8,
    "ai": 8,
    "tool": 6,
    "utility": 6,
    "archive": 6,
    "education": 8,
    "fdroid": 8,
    "fdroid_catalog": 8,
    "github_api": 4,
    "hackernews": 4,
}

GOOD_CATEGORIES = {
    "AI": 12,
    "Security": 12,
    "Datasets": 10,
    "Android": 10,
    "Education": 10,
    "Archives": 8,
    "Materials": 8,
    "Web Tools": 10,
}

BAD_NAME_FRAGMENTS = {
    "![",
    "[![",
    "badge",
    "license",
    "build status",
    "coverage",
}


def host_of(url: str) -> str:
    return urlparse(url).netloc.lower().removeprefix("www.")


def looks_junky(name: str) -> bool:
    lowered = (name or "").strip().lower()
    if len(lowered) < 4:
        return True
    return any(fragment in lowered for fragment in BAD_NAME_FRAGMENTS)


def rank_row(row: dict) -> tuple[int, str]:
    score = 0
    reasons = []

    host = host_of(row.get("url", ""))
    tags = [t.strip().lower() for t in (row.get("tags", "") or "").split(",") if t.strip()]
    category = (row.get("category", "") or "").strip()

    try:
        base_conf = int(row.get("confidence", "0") or "0")
    except ValueError:
        base_conf = 0

    score += min(base_conf, 50)
    if base_conf:
        reasons.append(f"base_conf={base_conf}")

    for domain, pts in GOOD_DOMAINS.items():
        if host == domain or host.endswith("." + domain):
            score += pts
            reasons.append(f"domain:{domain}+{pts}")
            break

    for tag in tags:
        if tag in GOOD_TAGS:
            score += GOOD_TAGS[tag]
            reasons.append(f"tag:{tag}+{GOOD_TAGS[tag]}")

    if category in GOOD_CATEGORIES:
        score += GOOD_CATEGORIES[category]
        reasons.append(f"category:{category}+{GOOD_CATEGORIES[category]}")

    name = (row.get("name", "") or "").strip().lower()

    if looks_junky(name):
        score -= 25
        reasons.append("junk_name-25")

    if "awesome" in name and "github.com" not in host:
        score -= 5
        reasons.append("weird_awesome-5")

    if row.get("description", "").strip().lower() == "discovered by atlas harvester":
        score -= 4
        reasons.append("generic_desc-4")

    score = max(0, min(score, 100))
    return score, " | ".join(reasons)


def bucket(score: int) -> str:
    if score >= 90:
        return "auto_promote"
    if score >= 80:
        return "review"
    return "ignore"


def main():
    if not INFILE.exists():
        raise SystemExit(f"Missing input: {INFILE}")

    with open(INFILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    ranked = []
    for row in rows:
        new_row = dict(row)
        score, reasons = rank_row(row)
        new_row["rank_score"] = str(score)
        new_row["rank_bucket"] = bucket(score)
        new_row["rank_reasons"] = reasons
        ranked.append(new_row)

    ranked.sort(key=lambda r: (-int(r["rank_score"]), r.get("name", "").lower()))

    fieldnames = list(ranked[0].keys()) if ranked else [
        "name", "url", "category", "subcategory", "tags", "description", "free_tier",
        "catalog_or_supplier", "status", "last_checked", "replacement_url", "notes",
        "source", "confidence", "rank_score", "rank_bucket", "rank_reasons"
    ]

    with open(OUTFILE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(ranked)

    auto_promote = sum(1 for r in ranked if r["rank_bucket"] == "auto_promote")
    review = sum(1 for r in ranked if r["rank_bucket"] == "review")
    ignore = sum(1 for r in ranked if r["rank_bucket"] == "ignore")

    print(f"Wrote {OUTFILE}")
    print(f"Ranked rows: {len(ranked)}")
    print(f"Auto-promote: {auto_promote}")
    print(f"Review: {review}")
    print(f"Ignore: {ignore}")


if __name__ == "__main__":
    main()