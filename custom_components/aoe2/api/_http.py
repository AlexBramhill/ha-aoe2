from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from functools import partial
from http import HTTPStatus
from typing import Any

import aiohttp

from ._backoff import with_exponential_backoff
from .errors import (
    AoeClientConnectionError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)
MAX_RETRIES = 5
FIRST_RETRY_DELAY_SECONDS = 5


async def get_json(
    session: aiohttp.ClientSession,
    url: str,
    params: dict[str, Any] | None = None,
    *,
    user_agent: str,
) -> dict[str, Any]:
    request = partial(_request_json, session, url, params, user_agent)
    return await _retry_transient_failures(request)


async def _retry_transient_failures(
    request: Callable[[], Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    """Rate limits aren't retried here; the coordinator honours their Retry-After."""
    return await with_exponential_backoff(
        request,
        retry_on=AoeClientConnectionError,
        max_retries=MAX_RETRIES,
        first_delay_seconds=FIRST_RETRY_DELAY_SECONDS,
    )


async def _request_json(
    session: aiohttp.ClientSession, url: str, params: dict[str, Any] | None, user_agent: str
) -> dict[str, Any]:
    async with (
        _connection_error_handler(url),
        session.get(
            url, params=params, headers={"User-Agent": user_agent}, timeout=REQUEST_TIMEOUT
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
            retry_after = _parse_retry_after(response.headers.get("Retry-After"))
            raise AoeClientRateLimitError(f"{url} rate limited", retry_after)
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


def _parse_retry_after(value: str | None) -> int | None:
    """Only the delta-seconds form; the rarely used HTTP-date form is ignored."""
    return int(value) if value and value.isdigit() else None
