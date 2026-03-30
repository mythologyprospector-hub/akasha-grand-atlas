from urllib.parse import urlparse,urlunparse
import re

DOMAIN_TRUST={
"gov":95,
"edu":92,
"org":80,
"github.com":85,
"archive.org":84,
"reddit.com":50
}

def normalize_url(url):
    p=urlparse(url.strip())
    netloc=p.netloc.lower()
    if netloc.startswith("www."): netloc=netloc[4:]
    path=re.sub(r"/+$","",p.path)
    return urlunparse((p.scheme or "https",netloc,path,"","",""))

def hostname(url):
    return urlparse(url).netloc.lower().removeprefix("www.")

def trust_score(url):
    host=hostname(url)
    for k,v in DOMAIN_TRUST.items():
        if host.endswith(k):
            return v
    return 60

def archive_fallback(url):
    return "https://web.archive.org/web/*/"+url

KNOWN_REPLACEMENTS = {}

def category_matches(category: str, url: str) -> bool:
    return True

def soft_delete_target():
    return ("Archives", "Soft Deleted")