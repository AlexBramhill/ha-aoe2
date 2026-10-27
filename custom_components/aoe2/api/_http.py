from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any

import aiohttp

from ._backoff import with_exponential_backoff
from .errors import (
    AoeClientConnectionError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
    AoeClientRetryError,
)

FIRST_RETRY_DELAY_SECONDS = 1.0
LONGEST_RETRY_WAIT_SECONDS = 10


@dataclass(frozen=True, slots=True)
class RequestPolicy:
    timeout_seconds: float
    max_retries: int


BACKGROUND_REQUESTS = RequestPolicy(timeout_seconds=15, max_retries=2)
INTERACTIVE_REQUESTS = RequestPolicy(timeout_seconds=10, max_retries=0)


async def get_json(
    session: aiohttp.ClientSession,
    url: str,
    params: dict[str, Any] | None = None,
    *,
    user_agent: str,
    policy: RequestPolicy,
) -> dict[str, Any]:
    request_timeout = aiohttp.ClientTimeout(total=policy.timeout_seconds)
    return await with_exponential_backoff(
        lambda: _request_json(session, url, params, user_agent, request_timeout),
        retry_on=AoeClientRetryError,
        max_retries=policy.max_retries,
        first_delay_seconds=FIRST_RETRY_DELAY_SECONDS,
        get_requested_delay=lambda error: error.retry_after,
        longest_wait_seconds=LONGEST_RETRY_WAIT_SECONDS,
    )


async def _request_json(
    session: aiohttp.ClientSession,
    url: str,
    params: dict[str, Any] | None,
    user_agent: str,
    request_timeout: aiohttp.ClientTimeout,
) -> dict[str, Any]:
    async with (
        _connection_error_handler(url),
        session.get(
            url, params=params, headers={"User-Agent": user_agent}, timeout=request_timeout
        ) as response,
    ):
        _raise_for_status(response)
        body = await _read_json(response)
    return _ensure_object(url, body)


@asynccontextmanager
async def _connection_error_handler(url: str) -> AsyncIterator[None]:
    try:
        yield
    except (aiohttp.ClientError, TimeoutError) as error:
        raise AoeClientConnectionError(f"Error fetching {url}: {error}") from error


def _raise_for_status(response: aiohttp.ClientResponse) -> None:
    url = response.url
    match response.status:
        case HTTPStatus.OK:
            return
        case HTTPStatus.NOT_FOUND:
            raise AoeClientNotFoundError(url)
        case HTTPStatus.TOO_MANY_REQUESTS:
            raise AoeClientRateLimitError(f"{url} rate limited", _get_retry_after(response))
        case HTTPStatus.SERVICE_UNAVAILABLE:
            raise AoeClientConnectionError(f"{url} is unavailable", _get_retry_after(response))
        case status if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            raise AoeClientConnectionError(f"{url} returned HTTP {status}")
        case status:
            raise AoeClientResponseError(f"{url} returned HTTP {status}")


async def _read_json(response: aiohttp.ClientResponse) -> Any:
    try:
        return await response.json(content_type=None)
    except ValueError as error:
        raise AoeClientResponseError(f"{response.url} returned invalid JSON") from error


def _ensure_object(url: str, body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise AoeClientResponseError(f"{url} returned {type(body).__name__}, expected object")
    return body


def _get_retry_after(response: aiohttp.ClientResponse) -> int | None:
    value = response.headers.get("Retry-After", "")
    return int(value) if value.isdecimal() else None
