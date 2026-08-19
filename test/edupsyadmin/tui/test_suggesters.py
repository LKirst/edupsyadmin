import pytest

from edupsyadmin.tui.suggesters import CategorySuggester

cats = ["ppb.inkl", "slbb.slb.sonstige"]


@pytest.mark.asyncio
async def test_category_suggester_prefix_match() -> None:
    """Test prefix matching in CategorySuggester."""
    suggester = CategorySuggester(cats, case_sensitive=False)
    assert await suggester.get_suggestion("ppb") == "ppb.inkl"


@pytest.mark.asyncio
async def test_category_suggester_segment_match() -> None:
    """Test segment matching (e.g. 'ink' matching 'ppb.inkl')."""
    suggester = CategorySuggester(cats, case_sensitive=False)
    assert await suggester.get_suggestion("ink") == "ppb.inkl"
    assert await suggester.get_suggestion("sonst") == "slbb.slb.sonstige"


@pytest.mark.asyncio
async def test_category_suggester_case_insensitive() -> None:
    """Test case-insensitive matching."""
    suggester = CategorySuggester(cats, case_sensitive=False)
    assert await suggester.get_suggestion("INK") == "ppb.inkl"


@pytest.mark.asyncio
async def test_category_suggester_no_match() -> None:
    """Test non-matching inputs."""
    suggester = CategorySuggester(["ppb.inkl"], case_sensitive=False)
    assert await suggester.get_suggestion("xyz") is None
    assert await suggester.get_suggestion("") is None
