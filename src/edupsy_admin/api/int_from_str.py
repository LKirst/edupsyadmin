import re


def extract_number(s: str) -> int | None:
    match = re.search(r"\d+", s)
    if match:
        return int(match.group())
    return None
