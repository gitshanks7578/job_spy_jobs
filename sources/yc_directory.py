"""Public YC directory discovery; no account or API key required."""
import re
from concurrent.futures import ThreadPoolExecutor
from html import unescape
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from .base import Company

BASE = "https://www.ycombinator.com"
INDUSTRIES = ("Developer%20Tools", "Infrastructure", "B2B", "Artificial%20Intelligence")
EXCLUDED = ("ycombinator.com", "youtube.com", "linkedin.com", "twitter.com", "x.com", "github.com", "facebook.com")


def _get(url):
    request = Request(url, headers={"User-Agent": "CompanyHunterMVP/1.0 (personal job research)"})
    with urlopen(request, timeout=8) as response:
        return response.read(1_500_000).decode("utf-8", "ignore")


def _text(html):
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html)))


def _location(text, config):
    for city in config["regions"].get("usa_cities", []):
        if city.lower() in text.lower(): return city, "USA"
    for city in config["regions"].get("eu_cities", []):
        if city.lower() in text.lower(): return city, "Europe"
    return "", ""


def _profile(slug, config):
    html = _get(f"{BASE}{slug}")
    text = _text(html)
    city, region = _location(text, config)
    if not region:
        return None
    title = re.search(r"<title>\s*(.*?)\s*-\s*Y Combinator", html, re.I | re.S)
    name = unescape(re.sub(r"<[^>]+>", "", title.group(1))).strip() if title else slug.rsplit("/", 1)[-1].replace("-", " ").title()
    candidates = re.findall(r'href=["\'](https?://[^"\']+)', html, re.I)
    website = next((link for link in candidates if not any(blocked in urlparse(link).netloc.lower() for blocked in EXCLUDED)), "")
    if not website:
        return None
    return Company(name=name, website=website, city=city, region=region, business_category="YC startup", discovery_source="yc_directory")


def discover(config: dict) -> list[Company]:
    try:
        slugs = []
        for industry in INDUSTRIES:
            html = _get(f"{BASE}/companies/industry/{industry}")
            slugs.extend(re.findall(r'href=["\'](/companies/(?!industry/)[^"\'?#]+)', html, re.I))
        slugs = list(dict.fromkeys(slugs))[:int(config.get("yc_daily_company_cap", 30))]
        with ThreadPoolExecutor(max_workers=8) as executor:
            return [company for company in executor.map(lambda slug: _profile(slug, config), slugs) if company]
    except Exception as exc:
        print(f"yc_directory: skipped ({exc})")
        return []
