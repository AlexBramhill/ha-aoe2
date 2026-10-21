from dataclasses import dataclass, field
from typing import cast

import aiohttp
import pytest

from custom_components.aoe2.api import (
    AoeClientConnectionError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
)
from custom_components.aoe2.api._http import _raise_for_status


@dataclass
class FakeResponse:
    status: int
    headers: dict[str, str] = field(default_factory=dict)
    url: str = "https://example.test"


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
