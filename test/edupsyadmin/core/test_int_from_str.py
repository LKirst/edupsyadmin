import pytest

from edupsyadmin.core.int_from_str import extract_number


@pytest.mark.parametrize(
    "input_string, expected",
    [
        ("5a", 5),
        ("E10b", 10),
        ("Vorklasse", None),
        ("12", 12),
    ],
)
def test_extract_number(input_string, expected):
    """Test extract_number with various inputs."""
    assert extract_number(input_string) == expected
