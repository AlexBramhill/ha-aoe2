class AoeClientError(Exception):
    pass


class AoeClientConnectionError(AoeClientError):
    pass


class AoeClientResponseError(AoeClientError):
    pass


class AoeClientNotFoundError(AoeClientError):
    pass


class AoeClientRateLimitError(AoeClientError):
    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after
