from difflib import SequenceMatcher
from sources.base import Company


def dedupe(companies: list[Company]) -> tuple[list[Company], int]:
    kept, duplicates = [], 0
    for company in companies:
        match = next((item for item in kept if company.domain and item.domain == company.domain), None)
        if not match and not company.domain:
            match = next((item for item in kept if SequenceMatcher(None, company.name.lower(), item.name.lower()).ratio() >= .92), None)
        if match:
            duplicates += 1
            for field in ("website", "public_email", "phone", "careers_page", "contact_page", "about_page", "linkedin", "github_org"):
                if not getattr(match, field) and getattr(company, field): setattr(match, field, getattr(company, field))
        else:
            kept.append(company)
    return kept, duplicates
