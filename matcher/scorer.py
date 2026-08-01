import re


def score(text: str, skills: dict) -> tuple[int, list[str]]:
    words = set(re.findall(r"[a-z0-9+#.]+", text.lower()))
    matched, total = [], 0
    for group, weight in (("must_have", 15), ("tech_stack", 5)):
        for keyword in skills.get(group, []):
            key = keyword.lower()
            if key in words:
                total += weight; matched.append(keyword)
    return min(total, 100), matched


def priority(score: int) -> str:
    return "High" if score >= 70 else "Medium" if score >= 40 else "Low"
