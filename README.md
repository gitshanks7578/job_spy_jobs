# Company Hunter MVP

CSV-only daily company discovery and resume-keyword matching for remote backend roles.

## Run it

From this folder, run:

```powershell
python run_daily.py --sample
```

`--sample` uses three known companies so you can verify the full pipeline without API access. Normal mode is non-interactive and cron/Task-Scheduler ready:

```powershell
python run_daily.py
```

On this Codex desktop machine, `python` is not currently on PATH; use the bundled interpreter path shown by Codex or install Python 3.10+.

## Configure it

- Add your skills in `skills.yaml`. Matching is deterministic: must-have terms score 15 each and tech-stack terms score 5 each, capped at 100.
- Paste your full resume into `master_resume.txt` for reference.
- YC and Hacker News are enabled by default and need no credentials. OpenStreetMap discovery is free too, but disabled by default because its public endpoint can be slow. Add `google_maps` to `enabled_sources` to enable it (the module retains its original name); `osm_daily_query_cap` controls its city queries.

All output is written to `output/latest/` and a date-stamped folder. `state/seen_companies.csv` preserves first-seen dates, so `new_today.csv` contains only fresh domains after the initial run.

## Source modules

Each module under `sources/` exposes `discover(config) -> list[Company]`; it can be replaced or extended independently. The map source uses OpenStreetMap. The `gmaps_companies.csv` filename is retained for compatibility with the supplied CSV contract, although its records are OpenStreetMap records.
