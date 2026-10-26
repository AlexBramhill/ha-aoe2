from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any, cast

import aiohttp
import pytest

from custom_components.aoe2.api import (
    AoeClientConnectionError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
)
from custom_components.aoe2.api._http import _raise_for_status, get_json
from tests.api.helpers import TEST_USER_AGENT


@dataclass
class FakeResponse:
    status: int
    headers: dict[str, str] = field(default_factory=dict)
    url: str = "https://example.test"


@dataclass
class FakeJsonResponse(FakeResponse):
    body: Any = None

    async def json(self, content_type: str | None = None) -> Any:
        return self.body


@dataclass
class RecordingSession:
    sent_headers: list[dict[str, str]] = field(default_factory=list)

    @asynccontextmanager
    async def get(self, url: str, **kwargs: Any) -> AsyncIterator[FakeJsonResponse]:
        self.sent_headers.append(kwargs.get("headers", {}))
        yield FakeJsonResponse(status=200, url=url, body={"ok": True})


def fake_response(status: int, headers: dict[str, str] | None = None) -> aiohttp.ClientResponse:
    """Status handling only reads status, headers and url, so a stand-in is enough."""
    return cast(aiohttp.ClientResponse, FakeResponse(status, headers or {}))


def rate_limited_response(retry_after: str | None) -> aiohttp.ClientResponse:
    headers = {"Retry-After": retry_after} if retry_after else {}
    return fake_response(429, headers)


def test_success_status_does_not_raise():
    # Given
    response = fake_response(200)

    # When / Then
    _raise_for_status(response)


@pytest.mark.parametrize(
    ("status", "expected_error"),
    [
        (404, AoeClientNotFoundError),
        (400, AoeClientResponseError),
        (500, AoeClientConnectionError),
        (503, AoeClientConnectionError),
    ],
)
def test_error_status_raises(status: int, expected_error: type[Exception]):
    # Given
    response = fake_response(status)

    # When / Then
    with pytest.raises(expected_error):
        _raise_for_status(response)


@pytest.mark.parametrize(
    ("retry_after_header", "retry_after_seconds"),
    [("30", 30), (None, None), ("Wed, 21 Oct 2026 07:28:00 GMT", None)],
)
def test_rate_limit_reads_retry_after(
    retry_after_header: str | None, retry_after_seconds: int | None
):
    # Given
    response = rate_limited_response(retry_after_header)

    # When
    with pytest.raises(AoeClientRateLimitError) as raised:
        _raise_for_status(response)

    # Then
    assert raised.value.retry_after == retry_after_seconds


async def test_requests_send_the_given_user_agent():
    # Given
    session = RecordingSession()

    # When
    await get_json(
        cast(aiohttp.ClientSession, session), "https://example.test/api", user_agent=TEST_USER_AGENT
    )

    # Then
    assert session.sent_headers == [{"User-Agent": TEST_USER_AGENT}]
