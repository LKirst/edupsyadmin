from collections.abc import Iterable

from textual.suggester import Suggester


class CategorySuggester(Suggester):
    """Suggester supporting prefix, segment, and substring matching."""

    def __init__(
        self, suggestions: Iterable[str], *, case_sensitive: bool = False
    ) -> None:
        super().__init__(case_sensitive=case_sensitive)
        self._suggestions = list(suggestions)

    async def get_suggestion(self, value: str) -> str | None:
        """Get suggestion for *value* using prefix, segment, or substring matching."""
        if not value:
            return None

        val_cmp = value if self.case_sensitive else value.casefold()

        # 1. Exact prefix match (highest priority)
        for s in self._suggestions:
            s_cmp = s if self.case_sensitive else s.casefold()
            if s_cmp.startswith(val_cmp):
                return s

        # 2. Dot-separated segment prefix match (e.g. 'ink' matching 'ppb.inkl')
        for s in self._suggestions:
            s_cmp = s if self.case_sensitive else s.casefold()
            parts = s_cmp.split(".")
            if any(part.startswith(val_cmp) for part in parts):
                return s

        # 3. Any substring match
        for s in self._suggestions:
            s_cmp = s if self.case_sensitive else s.casefold()
            if val_cmp in s_cmp:
                return s

        return None
