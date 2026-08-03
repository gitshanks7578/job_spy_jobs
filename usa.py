import csv
import time
import random
import pandas as pd
from jobspy import scrape_jobs

# ---------------------------------------
# CONFIG
# ---------------------------------------

SITES = [
    "indeed",
    "linkedin",
    # "google",
    # "zip_recruiter",
    # "glassdoor",
]

SEARCH_TERMS = [
    "backend engineer internship",
    "backend developer internship",
    "software engineer internship",
    "software developer internship",
    "junior software engineer",
]

LOCATIONS = [
    "Remote",
    "San Francisco, CA",
    "New York, NY",
    "Seattle, WA",
    "Austin, TX",
    "Boston, MA",
]

RESULTS_PER_SEARCH = 40

all_jobs = []

# ---------------------------------------
# SCRAPE
# ---------------------------------------

for site in SITES:

    print(f"\n========== {site.upper()} ==========")

    for term in SEARCH_TERMS:

        for location in LOCATIONS:

            print(f"{site} | {location} | {term}")

            kwargs = {
                "site_name": [site],
                "search_term": term,
                "location": location,
                "results_wanted": RESULTS_PER_SEARCH,
                "is_remote": True,
                "verbose": 0,
            }

            # Google Jobs
            if site == "google":
                kwargs["google_search_term"] = (
                    f"remote {term} jobs in {location}"
                )

            # Indeed / Glassdoor
            if site in ["indeed", "glassdoor"]:
                kwargs["country_indeed"] = "USA"

            try:

                jobs = scrape_jobs(**kwargs)

                if len(jobs):

                    jobs["searched_site"] = site
                    jobs["searched_location"] = location
                    jobs["search_term"] = term

                    all_jobs.append(jobs)

                    print(f"   + {len(jobs)} jobs")

                else:
                    print("   + 0 jobs")

            except Exception as e:
                print(e)

            # Delay to reduce rate limiting
            time.sleep(random.uniform(2.5, 5.5))

# ---------------------------------------
# EXPORT
# ---------------------------------------

if not all_jobs:
    print("No jobs found.")
    exit()

jobs = pd.concat(all_jobs, ignore_index=True)

# Remove duplicate postings
if "job_url" in jobs.columns:
    jobs.drop_duplicates(subset=["job_url"], inplace=True)
else:
    jobs.drop_duplicates(inplace=True)

# Keep only remote jobs
if "is_remote" in jobs.columns:
    jobs = jobs[jobs["is_remote"] == True]

# Remove huge / unnecessary columns
DROP_COLUMNS = [
    "description",
    "company_description",
    "company_logo",
]

jobs.drop(
    columns=[c for c in DROP_COLUMNS if c in jobs.columns],
    inplace=True,
)

# Sort newest first if available
if "date_posted" in jobs.columns:
    jobs.sort_values(
        by="date_posted",
        ascending=False,
        inplace=True,
    )

# Save CSV
jobs.to_csv(
    "usa_jobs.csv",
    index=False,
    quoting=csv.QUOTE_NONNUMERIC,
    escapechar="\\",
)

print("\n==============================")
print(f"Unique remote jobs: {len(jobs)}")
print("Saved -> usa_jobs.csv")
print("==============================")