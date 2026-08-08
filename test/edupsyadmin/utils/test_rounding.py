from edupsyadmin.utils.rounding import round_half_up


def test_round_half_up_integers() -> None:
    """Test round_half_up with default decimals (0) returning integers."""
    assert round_half_up(2.4) == 2
    assert round_half_up(2.5) == 3  # Standard round(2.5) would be 2 (banker's)
    assert round_half_up(3.5) == 4
    assert round_half_up(0.5) == 1
    assert round_half_up(0.49) == 0


def test_round_half_up_decimals() -> None:
    """Test round_half_up with specified decimal places."""
    assert round_half_up(1.234, 2) == 1.23
    assert round_half_up(1.235, 2) == 1.24
    assert round_half_up(2.555, 2) == 2.56
    assert round_half_up(10.12345, 4) == 10.1235
