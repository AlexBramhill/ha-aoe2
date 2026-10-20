from dataclasses import dataclass, field

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


def test_ok():
    _raise_for_status(FakeResponse(200))


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (404, AoeClientNotFoundError),
        (400, AoeClientResponseError),
        (500, AoeClientConnectionError),
        (503, AoeClientConnectionError),
    ],
)
def test_errors(status, expected):
    with pytest.raises(expected):
        _raise_for_status(FakeResponse(status))


@pytest.mark.parametrize(
    ("header", "expected"),
    [("30", 30), (None, None), ("Wed, 21 Oct 2026 07:28:00 GMT", None)],
)
def test_rate_limit(header, expected):
    headers = {"Retry-After": header} if header else {}
    with pytest.raises(AoeClientRateLimitError) as exc:
        _raise_for_status(FakeResponse(429, headers))
    assert exc.value.retry_after == expected
