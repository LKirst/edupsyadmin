from datetime import date, datetime


def to_bool_or_none(value: str | bool | int | None) -> bool | None:
    """
    Convert a string, int, or None to a boolean or None.
    - '1', 1, True -> True
    - '0', 0, False -> False
    - None, '' -> None
    - Any other string raises ValueError.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        if value == 1:
            return True
        if value == 0:
            return False
        raise ValueError(
            f"Integer value {value} cannot be converted to a boolean "
            "(expected 0 or 1).",
        )
    if isinstance(value, str):
        lower_value = value.lower().strip()
        if lower_value in ("true", "1"):
            return True
        if lower_value in ("false", "0"):
            return False
        raise ValueError(
            f"String value '{value}' cannot be converted to a boolean "
            f"(expected 'true', 'false', '0', or '1').",
        )
    raise TypeError(f"Value of type {type(value)} cannot be converted to a boolean.")


def to_int_or_none(value: str | int | None) -> int | None:
    """
    Convert a string or int to an int or None.
    - '123', 123 -> 123
    - None, '' -> None
    - Any other string raises ValueError.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError as e:
            raise ValueError(
                f"String value '{value}' cannot be converted to an integer.",
            ) from e
    raise TypeError(f"Value of type {type(value)} cannot be converted to an integer.")


def to_date_or_none(value: str | date | None) -> date | None:
    """
    Convert a string (YYYY-MM-DD) or date object to a date object or None.
    - '2023-01-01', date(2023, 1, 1) -> date(2023, 1, 1)
    - None, '' -> None
    - Invalid string format raises ValueError.
    """
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as e:
            raise ValueError(
                f"Invalid date format for '{value}'. Use YYYY-MM-DD.",
            ) from e
    raise TypeError(f"Value of type {type(value)} cannot be converted to a date.")
