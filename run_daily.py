"""Run with `python run_daily.py --sample` or schedule `python run_daily.py`."""
import argparse, asyncio, csv, importlib
from datetime import date
from pathlib import Path

from crawler.extractor import extract_contacts, extract_social_links, text_from_html
from crawler.fetch import fetch
from crawler.page_finder import find_pages
from matcher.resume_parser import load_skills
from matcher.scorer import priority, score
from sources.base import Company
from storage.csv_writer import write_csv
from storage.dedupe import dedupe
from storage.state import tag_new

SOURCES = ["yc_directory", "hn_whos_hiring", "google_maps", "producthunt", "accelerators", "directories"]

def read_config(path="config.yaml"):
    # Config intentionally only needs simple scalar/list YAML; PyYAML is optional.
    try:
        import yaml
        return yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except ImportError:
        import ast
        data, section = {}, None
        for raw in Path(path).read_text(encoding="utf-8").splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line: continue
            if line.endswith(":"): section = line[:-1]; data[section] = {}; continue
            key, value = line.split(":", 1); value = value.strip()
            target = data[section] if raw.startswith(" ") and section else data
            try: target[key.strip()] = ast.literal_eval(value)
            except (ValueError, SyntaxError):
                # Support the compact unquoted YAML lists used in config.yaml.
                if value.startswith("[") and value.endswith("]"):
                    target[key.strip()] = [item.strip().strip("'\"") for item in value[1:-1].split(",") if item.strip()]
                else: target[key.strip()] = value.strip('"')
        return data

def sample_companies():
    return [
        Company("GitLab", "https://about.gitlab.com", country="USA", city="San Francisco", region="USA", business_category="DevTools", discovery_source="sample"),
        Company("PostHog", "https://posthog.com", country="UK", city="London", region="Europe", business_category="Analytics", discovery_source="sample"),
        Company("Sentry", "https://sentry.io", country="USA", city="San Francisco", region="USA", business_category="DevTools", discovery_source="sample"),
    ]

async def crawl_company(company, config, skills, semaphore):
    if not company.website:
        return [], {"domain": company.domain, "reason": "no_website"}
    async with semaphore:
        html, error = await fetch(company.website, int(config["crawl_timeout_seconds"]), int(config["crawl_retries"]))
    if error: return [], {"domain": company.domain, "reason": error}
    pages = [(company.website, html)]
    for url in find_pages(company.website, html, int(config.get("crawl_pages_per_company", 3))):
        async with semaphore: page_html, _ = await fetch(url, int(config["crawl_timeout_seconds"]), int(config["crawl_retries"]))
        if page_html: pages.append((url, page_html))
    merged = " ".join(text_from_html(page) for _, page in pages)
    email, phone = extract_contacts(merged); company.public_email, company.phone = email, phone
    company.linkedin, company.github_org = extract_social_links(html)
    lower = merged.lower()
    company.remote_mention, company.backend_mention = "remote" in lower, "backend" in lower
    company.internship_mention, company.junior_mention = "intern" in lower, "junior" in lower
    for url, _ in pages:
        lurl = url.lower()
        if any(x in lurl for x in ("career", "job", "hiring", "join")): company.careers_page = company.careers_page or url
        if "contact" in lurl: company.contact_page = company.contact_page or url
        if "about" in lurl: company.about_page = company.about_page or url
    jobs = []
    for url, page in pages:
        text = text_from_html(page); value, words = score(text, skills)
        if any(word in text.lower() for word in ("career", "hiring", "job", "intern", "junior", "remote")):
            jobs.append({"name": company.name, "domain": company.domain, "page_url": url, "match_score": value, "matched_keywords": "; ".join(words), "priority": priority(value)})
    return jobs, None

async def main(sample=False):
    config, skills = read_config(), load_skills()
    companies = sample_companies() if sample else []
    if not sample:
        for source in config.get("enabled_sources", SOURCES):
            try: companies.extend(importlib.import_module(f"sources.{source}").discover(config))
            except Exception as exc: print(f"{source}: skipped ({exc})")
    raw_maps = [company.row() for company in companies if company.discovery_source == "openstreetmap"]
    companies, duplicate_count = dedupe(companies); tag_new(companies)
    # Keep every discovered company in the CSV, but crawl only the top bounded
    # slice. This prevents a large HN thread from turning into thousands of
    # website requests in one daily run.
    crawlable = companies[:int(config.get("crawl_company_cap", 40))]
    semaphore = asyncio.Semaphore(int(config["crawl_max_concurrency"]))
    results = await asyncio.gather(*(crawl_company(c, config, skills, semaphore) for c in crawlable))
    jobs, failed = [], []
    for job_rows, failure in results:
        jobs.extend(job_rows)
        if failure: failed.append(failure)
    max_scores = {row["domain"]: row["match_score"] for row in jobs}
    company_rows = [c.row() | {"match_score": max_scores.get(c.domain, 0)} for c in companies]
    company_rows.sort(key=lambda row: row["match_score"], reverse=True)
    root = Path(config["output_dir"]); destinations = [root / "latest", root / date.today().isoformat()]
    base_fields = list(Company.__dataclass_fields__) + ["match_score"]
    for destination in destinations:
        write_csv(destination / "companies.csv", company_rows, base_fields)
        write_csv(destination / "new_today.csv", [r for r in company_rows if r["new_today"]], base_fields)
        # Kept for backwards compatibility with the supplied output contract;
        # its data now comes from OpenStreetMap rather than Google Maps.
        write_csv(destination / "gmaps_companies.csv", raw_maps, list(Company.__dataclass_fields__))
        write_csv(destination / "jobs.csv", jobs, ["name", "domain", "page_url", "match_score", "matched_keywords", "priority"])
        write_csv(destination / "contacts.csv", [{k: r[k] for k in ("name", "public_email", "phone", "linkedin", "github_org")} for r in company_rows], ["name", "public_email", "phone", "linkedin", "github_org"])
        write_csv(destination / "failed.csv", failed, ["domain", "reason"])
    log = root.parent / "logs" / "run_log.csv"; log.parent.mkdir(exist_ok=True)
    new_log = not log.exists()
    with log.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["date", "total_found", "new_today_count", "duplicate_count", "failed_count"])
        if new_log: writer.writeheader()
        writer.writerow({"date": date.today().isoformat(), "total_found": len(companies), "new_today_count": sum(c.new_today for c in companies), "duplicate_count": duplicate_count, "failed_count": len(failed)})
    print(f"Done: {len(companies)} companies, {len(jobs)} hiring signals, {len(failed)} failures.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--sample", action="store_true")
    asyncio.run(main(parser.parse_args().sample))
