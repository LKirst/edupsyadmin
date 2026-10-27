from collections.abc import Iterable


class KeyValueParseError(ValueError):
    pass


def parse_key_value_pairs(pairs: Iterable[str], option_name: str) -> dict[str, str]:
    """Parse an iterable of ``key=value`` strings into a dictionary.

    Each item in ``pairs`` must contain exactly one ``=`` character. The
    key is stripped of surrounding whitespace and must be non-empty after
    stripping. The value is also stripped but may be empty. No further
    type coercion or normalization is applied to keys or values.

    :param pairs: Iterable of strings in the form ``key=value``.
    :type pairs: Iterable[str]
    :param option_name: Name of the source option/argument, used only to
        build a descriptive error message.
    :type option_name: str
    :returns: Mapping of parsed, stripped keys to their stripped values.
    :rtype: dict[str, str]
    :raises ValueError: If any entries are malformed (not exactly one
        ``=``, or an empty key after stripping). The message lists all
        offending entries.
    """
    result: dict[str, str] = {}
    bad: list[str] = []

    for s in pairs:
        # Must contain exactly one '='
        if s.count("=") != 1:
            bad.append(s)
            continue

        key, value = s.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not key:
            bad.append(s)
            continue

        result[key] = value

    if bad:
        raise ValueError(
            f"Malformed {option_name} entries: {', '.join(bad)}. "
            "Use exactly one '=' with a non-empty key (e.g., key=value).",
        )

    return result
