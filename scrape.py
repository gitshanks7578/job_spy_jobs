# import csv
# import time
# import pandas as pd
# from jobspy import scrape_jobs

# # ----------------------------
# # CONFIGURATION
# # ----------------------------

# SITES = [
#     "linkedin",
#     "indeed",
#     "google",
#     "zip_recruiter",
#     "glassdoor",
#     "bayt",
#     "naukri",
#     "bdjobs",
# ]

# SEARCH_TERMS = [
#     # Backend
#     "backend engineer",
#     "backend developer",
#     "backend software engineer",
#     "server side engineer",
#     "api engineer",
#     "api developer",
#     "platform engineer",
#     "platform developer",
#     "microservices engineer",

#     # Node.js
#     "node developer",
#     "node.js developer",
#     "node engineer",
#     "express developer",

#     # Software Engineering
#     "software engineer",
#     "software developer",
#     "software engineer intern",
#     "software developer intern",
#     "graduate software engineer",
#     "entry level software engineer",
#     "junior software engineer",
#     "associate software engineer",

#     # Full Stack
#     "full stack engineer",
#     "full stack developer",

#     # Internship
#     "backend internship",
#     "software engineering internship",
#     "software developer internship",
#     "computer science internship",

#     # Infrastructure
#     "cloud engineer",
#     "devops engineer",
#     "site reliability engineer",

#     # Data
#     "data engineer",

#     # Languages
#     "python developer",
#     "java developer",
#     "golang developer",
#     "c++ developer",
# ]

# LOCATIONS = [
#     "Remote",

#     # North America
#     "United States",
#     "Canada",

#     # UK
#     "United Kingdom",
#     "Ireland",

#     # Europe
#     "Netherlands",
#     "Germany",
#     "Sweden",
#     "Denmark",
#     "Norway",
#     "Finland",
#     "Estonia",
#     "Poland",
#     "Portugal",
#     "Czech Republic",

#     # APAC
#     "Singapore",
#     "Australia",
#     "New Zealand",

#     # Middle East
#     "United Arab Emirates",
# ]

# INDEED_COUNTRIES = [
#     "USA",
#     "Canada",
#     "UK",
#     "Ireland",
#     "Netherlands",
#     "Germany",
#     "Sweden",
#     "Denmark",
#     "Norway",
#     "Finland",
#     "Poland",
#     "Portugal",
#     "Czech Republic",
#     "Singapore",
#     "Australia",
#     "New Zealand",
#     "United Arab Emirates",
# ]

# RESULTS_PER_SEARCH = 50
# HOURS_OLD = 168  # last 7 days

# # ----------------------------
# # SCRAPER
# # ----------------------------

# all_jobs = []

# for site in SITES:

#     print(f"\n========================")
#     print(f"Searching {site.upper()}")
#     print(f"========================")

#     for term in SEARCH_TERMS:

#         for location in LOCATIONS:

#             try:

#                 kwargs = {
#                     "site_name": [site],
#                     "search_term": term,
#                     "location": location,
#                     "results_wanted": RESULTS_PER_SEARCH,
#                     "verbose": 1,
#                 }

#                 # Google has its own search syntax
#                 if site == "google":
#                     kwargs["google_search_term"] = (
#                         f"{term} jobs in {location}"
#                     )

#                 # Indeed / Glassdoor require a country
#                 if site in ["indeed", "glassdoor"]:

#                     for country in INDEED_COUNTRIES:

#                         try:
#                             jobs = scrape_jobs(
#                                 **kwargs,
#                                 country_indeed=country,
#                             )

#                             if len(jobs):
#                                 jobs["search_term"] = term
#                                 jobs["searched_location"] = location
#                                 jobs["searched_country"] = country
#                                 jobs["searched_site"] = site
#                                 all_jobs.append(jobs)

#                             print(
#                                 f"[{site}] {country:<18} | {location:<22} | {term:<35} -> {len(jobs)} jobs"
#                             )

#                             time.sleep(2)

#                         except Exception as e:
#                             print(e)

#                     continue

#                 jobs = scrape_jobs(**kwargs)

#                 if len(jobs):
#                     jobs["search_term"] = term
#                     jobs["searched_location"] = location
#                     jobs["searched_site"] = site
#                     all_jobs.append(jobs)

#                 print(
#                     f"[{site}] {location:<22} | {term:<35} -> {len(jobs)} jobs"
#                 )

#                 time.sleep(2)

#             except Exception as e:
#                 print(e)

# # ----------------------------
# # EXPORT
# # ----------------------------

# if not all_jobs:
#     print("\nNo jobs found.")
#     exit()

# jobs = pd.concat(all_jobs, ignore_index=True)

# # Remove duplicates
# if "job_url" in jobs.columns:
#     jobs.drop_duplicates(subset=["job_url"], inplace=True)
# else:
#     jobs.drop_duplicates(inplace=True)

# jobs.to_csv(
#     "jobs.csv",
#     index=False,
#     quoting=csv.QUOTE_NONNUMERIC,
#     escapechar="\\",
# )

# print("\n===================================")
# print(f"Total unique jobs: {len(jobs)}")
# print("Saved to jobs.csv")
# print("===================================")