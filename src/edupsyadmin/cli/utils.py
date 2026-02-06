import importlib.util
import sys
import types
from collections.abc import Iterable


# Lazy import utility function
def lazy_import(name: str) -> types.ModuleType:
    """
    Lazy import utility function. This function is from the Python
    documentation
    (https://docs.python.org/3/library/importlib.html#implementing-lazy-imports).

    :param name: The name of the module to be lazily imported.
    :return: The lazily imported module.
    """
    spec = importlib.util.find_spec(name)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot find module '{name}'")

    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


class KeyValueParseError(ValueError):
    pass


def parse_key_value_pairs(pairs: Iterable[str], option_name: str) -> dict[str, str]:
    """
    Parse an iterable of 'key=value' strings into a dict.

    Rules:
    - Exactly one '=' per pair
    - Key must be non-empty after stripping
    - Value may be empty; spaces allowed
    - No further type coercion or normalization

    Raises:
    - ValueError with a concise message listing the malformed entries
    """
    result: dict[str, str] = {}
    bad: list[str] = []

    for raw in pairs:
        s = str(raw)
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
            "Use exactly one '=' with a non-empty key (e.g., key=value)."
        )

    return result
