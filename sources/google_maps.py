"""Free OpenStreetMap company discovery via the public Overpass API.

The module name is retained for compatibility with the original spec.  No
Google account, key, billing profile, map UI, or Leaflet is required.
"""
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from .base import Company


def discover(config: dict) -> list[Company]:
    cities = [(x, "USA") for x in config["regions"].get("usa_cities", [])] + [(x, "Europe") for x in config["regions"].get("eu_cities", [])]
    cap, found, queries = int(config.get("osm_daily_query_cap", len(cities))), [], 0
    for city, region in cities:
        if queries >= cap:
            return found
        queries += 1
        # Search broadly for technology offices inside the named city area.
        overpass = f'''[out:json][timeout:25];area["name"="{city}"]["boundary"="administrative"]->.a;(nwr["office"~"(it|company)",i](area.a);nwr["industry"~"software|information technology",i](area.a););out center tags;'''
        try:
            request = Request("https://overpass-api.de/api/interpreter", data=urlencode({"data": overpass}).encode(),
                              headers={"User-Agent": "CompanyHunterMVP/1.0 (personal job research)"})
            data = json.load(urlopen(request, timeout=12))
        except Exception:
            continue
        for item in data.get("elements", []):
            tags = item.get("tags", {})
            name = tags.get("name", "")
            website = tags.get("website") or tags.get("contact:website", "")
            if not name or not website:
                continue
            found.append(Company(name=name, website=website, city=city, region=region,
                country=tags.get("addr:country", ""), business_category=tags.get("industry", tags.get("office", "software")),
                gmaps_url=f"https://www.openstreetmap.org/{item.get('type')}/{item.get('id')}",
                public_email=tags.get("email", tags.get("contact:email", "")), phone=tags.get("phone", tags.get("contact:phone", "")),
                discovery_source="openstreetmap"))
    return found
