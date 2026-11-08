from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from http import HTTPStatus

import aiohttp
from aiohttp.typedefs import Query
from pydantic import BaseModel, ValidationError

from custom_components.aoe2.api._backoff import with_exponential_backoff
from custom_components.aoe2.api._errors import (
    AoeClientConnectionError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
    AoeClientRetryableError,
    AoeClientServerError,
)

FIRST_RETRY_DELAY_SECONDS = 1.0
LONGEST_RETRY_WAIT_SECONDS = 10
USER_AGENT = "ha-aoe2/{version} (+https://github.com/AlexBramhill/ha-aoe2)"


@dataclass(frozen=True, slots=True)
class RequestPolicy:
    timeout_seconds: float
    max_retries: int


BACKGROUND_REQUESTS = RequestPolicy(timeout_seconds=15, max_retries=2)
INTERACTIVE_REQUESTS = RequestPolicy(timeout_seconds=10, max_retries=0)


async def get_response[Response: BaseModel](
    session: aiohttp.ClientSession,
    url: str,
    response_type: type[Response],
    params: Query | None = None,
    *,
    version: str,
    policy: RequestPolicy,
) -> Response:
    user_agent = USER_AGENT.format(version=version)
    request_timeout = aiohttp.ClientTimeout(total=policy.timeout_seconds)
    body = await with_exponential_backoff(
        lambda: _get_response_body(session, url, params, user_agent, request_timeout),
        retry_on=AoeClientRetryableError,
        max_retries=policy.max_retries,
        first_delay_seconds=FIRST_RETRY_DELAY_SECONDS,
        get_requested_delay=lambda error: error.retry_after,
        longest_wait_seconds=LONGEST_RETRY_WAIT_SECONDS,
    )
    return _get_validated_response(url, body, response_type)


async def _get_response_body(
    session: aiohttp.ClientSession,
    url: str,
    params: Query | None,
    user_agent: str,
    request_timeout: aiohttp.ClientTimeout,
) -> str:
    async with (
        _translate_connection_errors(url),
        session.get(
            url, params=params, headers={"User-Agent": user_agent}, timeout=request_timeout
        ) as response,
    ):
        raise_for_status(response)
        return await response.text()


def _get_validated_response[Response: BaseModel](
    url: str, body: str, response_type: type[Response]
) -> Response:
    try:
        return response_type.model_validate_json(body)
    except ValidationError as error:
        raise AoeClientResponseError(f"{url} returned an unexpected response: {error}") from error


@asynccontextmanager
async def _translate_connection_errors(url: str) -> AsyncGenerator[None]:
    try:
        yield
    except (aiohttp.ClientError, TimeoutError) as error:
        raise AoeClientConnectionError(f"Error fetching {url}: {error}") from error


def raise_for_status(response: aiohttp.ClientResponse) -> None:
    url = response.url
    match response.status:
        case HTTPStatus.OK:
            return
        case HTTPStatus.NOT_FOUND:
            raise AoeClientNotFoundError(url)
        case HTTPStatus.TOO_MANY_REQUESTS:
            raise AoeClientRateLimitError(f"{url} rate limited", _get_retry_after(response))
        case HTTPStatus.SERVICE_UNAVAILABLE:
            raise AoeClientServerError(f"{url} is unavailable", _get_retry_after(response))
        case status if status >= HTTPStatus.INTERNAL_SERVER_ERROR:
            raise AoeClientServerError(f"{url} returned HTTP {status}")
        case status:
            raise AoeClientResponseError(f"{url} returned HTTP {status}")


def _get_retry_after(response: aiohttp.ClientResponse) -> int | None:
    value = response.headers.get("Retry-After", "")
    return int(value) if value.isdecimal() else None
