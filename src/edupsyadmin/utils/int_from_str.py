import re


def extract_number(s: str) -> int | None:
    match = re.search(r"\d+", s)
    if match:
        try:
            return int(match.group())
        except ValueError as e:
            raise ValueError(f"Error converting '{match.group}' to int") from e
    return None
