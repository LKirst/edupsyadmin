from decimal import ROUND_HALF_UP, Decimal
from typing import overload


@overload
def round_half_up(value: float) -> int: ...


@overload
def round_half_up(value: float, decimals: int) -> float: ...


def round_half_up(value: float, decimals: int = 0) -> int | float:
    """Round *value* to *decimals* places using round-half-up.

    :param value: The number to round.
    :param decimals: Number of decimal places (default: 0).
    :returns: Rounded int or float.
    """
    quantizer = Decimal(10) ** -decimals  # e.g. Decimal("0.01") for 2
    res = Decimal(str(value)).quantize(quantizer, rounding=ROUND_HALF_UP)
    if decimals <= 0:
        return int(res)
    return float(res)
