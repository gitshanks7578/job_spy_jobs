from .base import Company

def discover(config: dict) -> list[Company]:
    # Keep sources independently replaceable; live directory scraping is intentionally avoided.
    return []
