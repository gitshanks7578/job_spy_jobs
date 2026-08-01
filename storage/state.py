import csv
from datetime import date
from pathlib import Path

FIELDS = ["domain", "first_seen_date", "last_seen_date"]

def tag_new(companies, path: str = "state/seen_companies.csv"):
    file = Path(path); file.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if file.exists():
        with file.open(encoding="utf-8", newline="") as handle:
            existing = {row["domain"]: row for row in csv.DictReader(handle) if row.get("domain")}
    today = date.today().isoformat()
    for company in companies:
        prior = existing.get(company.domain)
        company.new_today = not bool(prior)
        company.first_seen = prior["first_seen_date"] if prior else today
        if company.domain: existing[company.domain] = {"domain": company.domain, "first_seen_date": company.first_seen, "last_seen_date": today}
    with file.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS); writer.writeheader(); writer.writerows(existing.values())
    return companies
