from html.parser import HTMLParser
from urllib.parse import urljoin


KEYWORDS = ("career", "job", "hiring", "join", "about", "contact", "team", "engineering", "blog", "api")

class LinkFinder(HTMLParser):
    def __init__(self): super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href: self.links.append(href)

def find_pages(homepage: str, html: str, limit: int = 8) -> list[str]:
    parser = LinkFinder(); parser.feed(html)
    urls = [urljoin(homepage, link) for link in parser.links if any(k in link.lower() for k in KEYWORDS)]
    return list(dict.fromkeys(urls))[:limit]
