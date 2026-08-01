import re


def score(text: str, skills: dict) -> tuple[int, list[str]]:
    # Keep technology punctuation (Node.js / Express.js) but normalize spaces,
    # so multi-word skills such as "REST API" and "entry-level" match too.
    normalized = re.sub(r"\s+", " ", text.lower())
    words = set(re.findall(r"[a-z0-9+#.]+", normalized))
    matched, total = [], 0
    for group, weight in (("must_have", 15), ("tech_stack", 5)):
        for keyword in skills.get(group, []):
            key = keyword.lower()
            if (" " in key or "-" in key) and re.search(r"(?<!\w)" + re.escape(key) + r"(?!\w)", normalized):
                total += weight; matched.append(keyword)
            elif key in words:
                total += weight; matched.append(keyword)
    return min(total, 100), matched


def priority(score: int) -> str:
    return "High" if score >= 70 else "Medium" if score >= 40 else "Low"
