class AoeClientError(Exception):
    pass


class AoeClientNotFoundError(AoeClientError):
    pass


class AoeClientResponseError(AoeClientError):
    pass


class AoeClientRetryableError(AoeClientError):
    def __init__(self, message: str, retry_after: int | None = None) -> None:
        super().__init__(message)
        self.retry_after: int | None = retry_after


class AoeClientConnectionError(AoeClientRetryableError):
    pass


class AoeClientServerError(AoeClientRetryableError):
    pass


class AoeClientRateLimitError(AoeClientRetryableError):
    pass
