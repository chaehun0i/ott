"""Stable search business errors."""


class SearchError(ValueError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


class EmbeddingUnavailable(SearchError):
    def __init__(self, code: str = "SEARCH_EMBEDDING_UNAVAILABLE") -> None:
        super().__init__(code, "semantic search is temporarily unavailable", retryable=True)


class CursorError(SearchError):
    def __init__(self) -> None:
        super().__init__("SEARCH_CURSOR_INVALID", "cursor is invalid")
