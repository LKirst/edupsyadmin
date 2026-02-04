import pytest

from edupsyadmin.utils.taetigkeitsbericht_check_key import (
    check_keyword,
    get_taet_categories,
)


def test_get_taet_categories_real_file():
    """Test get_taet_categories with the actual data file."""
    categories = get_taet_categories()
    assert isinstance(categories, set)
    # Check for a known category
    assert "slbb.slb.sonstige" in categories


@pytest.fixture
def mock_get_categories(monkeypatch):
    """Mock get_taet_categories to return a fixed set of keywords."""
    test_keywords = {"key1", "key2", "key3.a"}
    monkeypatch.setattr(
        "edupsyadmin.utils.taetigkeitsbericht_check_key.get_taet_categories",
        lambda: test_keywords,
    )
    return test_keywords


def test_check_keyword_valid(mock_get_categories):
    """Test check_keyword with a valid keyword."""
    assert check_keyword("key1") == "key1"


def test_check_keyword_empty(mock_get_categories):
    """Test check_keyword with empty or None keyword."""
    assert check_keyword("") == ""
    assert check_keyword(None) is None


def test_check_keyword_invalid(mock_get_categories):
    """Test that check_keyword raises ValueError for an invalid keyword."""
    with pytest.raises(ValueError) as excinfo:
        check_keyword("invalid_key")
    assert "Invalid keyword: 'invalid_key'" in str(excinfo.value)
