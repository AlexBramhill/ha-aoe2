from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from http import HTTPStatus
from typing import Any

import aiohttp

from .errors import (
    AoeClientConnectionError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
)

REQUEST_TIMEOUT = aiohttp.ClientTimeout(total=15)


async def get_json(
    session: aiohttp.ClientSession, url: str, params: dict[str, Any] | None = None
) -> dict[str, Any]:
    async with (
        _connection_error_handler(url),
        session.get(url, params=params, timeout=REQUEST_TIMEOUT) as response,
    ):
        _raise_for_status(response)
        body = await _read_json(response)
    return _ensure_object(url, body)


@asynccontextmanager
async def _connection_error_handler(url: str) -> AsyncIterator[None]:
    try:
        yield
    except (aiohttp.ClientError, TimeoutError) as err:
        raise AoeClientConnectionError(f"Error fetching {url}: {err}") from err


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
    except ValueError as err:
        raise AoeClientResponseError(f"{response.url} returned invalid JSON") from err


def _ensure_object(url: str, body: Any) -> dict[str, Any]:
    if not isinstance(body, dict):
        raise AoeClientResponseError(f"{url} returned {type(body).__name__}, expected object")
    return body


def _parse_retry_after(value: str | None) -> int | None:
    """Only the delta-seconds form; the rarely used HTTP-date form is ignored."""
    return int(value) if value and value.isdigit() else None
