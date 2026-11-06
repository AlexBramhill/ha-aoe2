class AoeClientError(Exception):
    pass


class AoeClientRetryError(AoeClientError):
    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class AoeClientConnectionError(AoeClientRetryError):
    pass


class AoeClientResponseError(AoeClientError):
    pass


class AoeClientNotFoundError(AoeClientError):
    pass


class AoeClientRateLimitError(AoeClientRetryError):
    pass
