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
- Discovery uses the free public OpenStreetMap Overpass API; no API key, billing account, Google Maps, or Leaflet is needed. `osm_daily_query_cap` controls how many city queries run per day. Please keep it modest, as Overpass is community-operated infrastructure.

All output is written to `output/latest/` and a date-stamped folder. `state/seen_companies.csv` preserves first-seen dates, so `new_today.csv` contains only fresh domains after the initial run.

## Source modules

Each module under `sources/` exposes `discover(config) -> list[Company]`; it can be replaced or extended independently. The map source now uses OpenStreetMap. The `gmaps_companies.csv` filename is retained for compatibility with the supplied CSV contract, although its records are OpenStreetMap records.
