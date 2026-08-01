# Company Hunter MVP

CSV-only daily company discovery and resume-keyword matching for remote backend roles. The active pipeline is Node.js + Crawlee + Playwright.

## Run it

From this folder, run:

```powershell
pnpm install
pnpm exec playwright install chromium
pnpm run sample
```

`pnpm run sample` uses three known companies. The live, non-interactive daily run is:

```powershell
pnpm run daily
```

On GitHub Codespaces, use `pnpm exec playwright install --with-deps chromium` instead; it installs the required Linux browser libraries too.

## Configure it

- Add your skills in `skills.yaml`. Matching is deterministic: must-have terms score 15 each and tech-stack terms score 5 each, capped at 100.
- Paste your full resume into `master_resume.txt` for reference.
- YC and Hacker News are enabled by default and need no credentials. The limits in `hunter.config.json` cap browsing at 30 companies, 2 discovered links per company, 80 total browser requests, 5 concurrent pages, and 10 seconds per request.

All output is written to `output/latest/` and a date-stamped folder. `state/seen_companies.csv` preserves first-seen dates, so `new_today.csv` contains only fresh domains after the initial run.

## Source modules

`src/sources.js` discovers YC and Hacker News companies. `src/websiteCrawler.js` uses Crawlee's Playwright crawler to render homepages and targeted careers/about/team/engineering links; it extracts contacts and hiring signals. `src/storage.js` writes CSVs to `output/latest/` and dated output folders.
