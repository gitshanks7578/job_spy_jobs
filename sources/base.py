from dataclasses import asdict, dataclass, field
from datetime import date
from urllib.parse import urlparse


def normalise_domain(url: str) -> str:
    candidate = (url or "").strip().lower()
    if candidate and "://" not in candidate:
        candidate = "https://" + candidate
    host = urlparse(candidate).netloc.split("@")[-1].split(":")[0]
    return host.removeprefix("www.")


@dataclass
class Company:
    name: str
    website: str
    domain: str = ""
    country: str = ""
    city: str = ""
    region: str = ""
    business_category: str = ""
    gmaps_url: str = ""
    gmaps_rating: float | None = None
    gmaps_review_count: int | None = None
    public_email: str = ""
    phone: str = ""
    careers_page: str = ""
    contact_page: str = ""
    about_page: str = ""
    linkedin: str = ""
    github_org: str = ""
    remote_mention: bool = False
    backend_mention: bool = False
    internship_mention: bool = False
    junior_mention: bool = False
    tech_stack: list[str] = field(default_factory=list)
    discovery_source: str = ""
    date_discovered: str = ""
    first_seen: str = ""
    new_today: bool = False

    def __post_init__(self):
        self.domain = normalise_domain(self.domain or self.website)
        self.date_discovered = self.date_discovered or date.today().isoformat()

    def row(self):
        result = asdict(self)
        result["tech_stack"] = "; ".join(self.tech_stack)
        return result
