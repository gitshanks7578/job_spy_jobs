import re
from html import unescape
from urllib.parse import urlparse

EMAIL = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
PHONE = re.compile(r"(?:\+?\d[\d .()\-]{7,}\d)")

def text_from_html(html: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", html))).strip()

def extract_contacts(text: str):
    return (next(iter(EMAIL.findall(text)), ""), next(iter(PHONE.findall(text)), ""))

def extract_social_links(html: str):
    links = re.findall(r'https?://[^"\' <>]+', html)
    linkedin = next((x for x in links if "linkedin.com" in x), "")
    github = next((x for x in links if "github.com" in x), "")
    return linkedin, github
