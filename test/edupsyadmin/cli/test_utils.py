import pytest

from edupsyadmin.cli.utils import parse_key_value_pairs


@pytest.mark.parametrize(
    "pairs, expected",
    [
        ([], {}),
        (["a=1"], {"a": "1"}),
        (["a=1", "b=2"], {"a": "1", "b": "2"}),
        (["a = 1"], {"a": "1"}),  # trims spaces around key and value
        (
            [" key = value with spaces "],
            {"key": "value with spaces"},
        ),  # trims key/value
        (["a="], {"a": ""}),  # empty value is allowed
        (["notes=needs extra time"], {"notes": "needs extra time"}),  # spaces in value
    ],
)
def test_parse_key_value_pairs_happy_paths(pairs, expected):
    assert parse_key_value_pairs(pairs, option_name="--opt") == expected


@pytest.mark.parametrize(
    "pairs, bad_entries",
    [
        (["foo"], ["foo"]),  # missing '='
        (["=bar"], ["=bar"]),  # empty key after strip
        ([" a =1", "b"], ["b"]),  # mixed: one ok, one bad
        (["a==b"], ["a==b"]),  # multiple '=' not allowed
        (["a=1", "==", "x=y=z"], ["==", "x=y=z"]),  # multiple bad entries reported
        (["   =   "], ["   =   "]),  # whitespace-only key
    ],
)
def test_parse_key_value_pairs_reports_bad_entries(pairs, bad_entries):
    option_name = "--opt"
    with pytest.raises(ValueError) as exc:
        parse_key_value_pairs(pairs, option_name=option_name)

    msg = str(exc.value)
    # Asserts the message structure and that all bad entries are listed
    assert msg.startswith("Malformed --opt entries: ")
    for bad in bad_entries:
        assert bad in msg
    assert "Use exactly one '=' with a non-empty key (e.g., key=value)." in msg
