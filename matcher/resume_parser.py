from pathlib import Path


def load_skills(path: str = "skills.yaml") -> dict:
    """Read the small list-based YAML shape without an external PyYAML dependency."""
    result, current = {}, None
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line: continue
        if ":" in line:
            key, value = line.split(":", 1); current = key.strip(); value = value.strip()
            if value.startswith("["):
                result[current] = [x.strip().strip("'\"") for x in value.strip("[]").split(",") if x.strip()]
            else: result[current] = []
    return result
