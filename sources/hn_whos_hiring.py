"""Public, no-key Hacker News 'Who is hiring?' discovery."""
import json
import re
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .base import Company

API = "https://hacker-news.firebaseio.com/v0"
URL = re.compile(r'https?://[^\s"<>]+', re.I)
EU_WORDS = ("europe", "european", "eu ", "uk", "united kingdom", "germany", "france", "netherlands", "spain", "portugal", "ireland", "sweden", "denmark", "finland", "poland")
US_WORDS = (" usa", "u.s.", "united states", "us-only", " us ")


def _get(path):
    request = Request(f"{API}/{path}", headers={"User-Agent": "CompanyHunterMVP/1.0"})
    with urlopen(request, timeout=8) as response:
        return json.load(response)


def _region(text):
    lower = f" {text.lower()} "
    if any(word in lower for word in EU_WORDS): return "Europe"
    if any(word in lower for word in US_WORDS): return "USA"
    return ""


def _company_from_comment(comment):
    text = unescape(re.sub(r"<[^>]+>", " ", comment.get("text", "")))
    region = _region(text)
    if not region:
        return None
    urls = URL.findall(text)
    url = next((candidate.rstrip(".,)") for candidate in urls if urlparse(candidate).netloc and "news.ycombinator.com" not in candidate), "")
    if not url:
        return None
    domain = urlparse(url).netloc.removeprefix("www.")
    prefix = text.split(url, 1)[0].strip(" -:|\n")
    name = re.split(r"\s+(?:is|are|—|-|\|)", prefix, maxsplit=1)[0][:100] or domain.split(".")[0].title()
    return Company(name=name, website=url, domain=domain, region=region,
                   business_category="Software", discovery_source="hn_whos_hiring")


def discover(config: dict) -> list[Company]:
    try:
        ask_ids = _get("askstories.json")[:100]
        with ThreadPoolExecutor(max_workers=12) as executor:
            stories = list(executor.map(lambda item_id: _get(f"item/{item_id}.json"), ask_ids))
        thread = next((story for story in stories if story and "who is hiring" in story.get("title", "").lower()), None)
        if not thread:
            return []
        comment_ids = thread.get("kids", [])[:int(config.get("hn_comment_cap", 150))]
        with ThreadPoolExecutor(max_workers=12) as executor:
            comments = list(executor.map(lambda item_id: _get(f"item/{item_id}.json"), comment_ids))
        return [company for company in (_company_from_comment(comment or {}) for comment in comments) if company]
    except Exception as exc:
        print(f"hn_whos_hiring: skipped ({exc})")
        return []
