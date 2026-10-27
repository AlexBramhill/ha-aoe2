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
    _backoff,
)
from custom_components.aoe2.api._http import (
    BACKGROUND_REQUESTS,
    INTERACTIVE_REQUESTS,
    LONGEST_RETRY_WAIT_SECONDS,
    RequestPolicy,
    _raise_for_status,
    get_json,
)
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
    sent_timeouts: list[aiohttp.ClientTimeout] = field(default_factory=list)

    @asynccontextmanager
    async def get(self, url: str, **kwargs: Any) -> AsyncIterator[FakeJsonResponse]:
        self.sent_headers.append(kwargs.get("headers", {}))
        self.sent_timeouts.append(kwargs["timeout"])
        yield FakeJsonResponse(status=200, url=url, body={"ok": True})


@dataclass
class FlakySession:
    """Answers with the given statuses in order, then 200 once they run out."""

    statuses: list[int]
    headers: dict[str, str] = field(default_factory=dict)
    attempts: int = 0

    @asynccontextmanager
    async def get(self, url: str, **kwargs: Any) -> AsyncIterator[FakeJsonResponse]:
        status = self.statuses[self.attempts] if self.attempts < len(self.statuses) else 200
        self.attempts += 1
        yield FakeJsonResponse(status=status, headers=self.headers, url=url, body={"ok": True})


@pytest.fixture
def no_backoff_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    async def skip_sleep(delay: float) -> None:
        pass

    monkeypatch.setattr(_backoff.asyncio, "sleep", skip_sleep)


async def get_from(
    session: FlakySession | RecordingSession, policy: RequestPolicy = BACKGROUND_REQUESTS
) -> dict[str, Any]:
    return await get_json(
        cast(aiohttp.ClientSession, session),
        "https://example.test/api",
        user_agent=TEST_USER_AGENT,
        policy=policy,
    )


def fake_response(status: int, headers: dict[str, str] | None = None) -> aiohttp.ClientResponse:
    """Status handling only reads status, headers and url, so a stand-in is enough."""
    return cast(aiohttp.ClientResponse, FakeResponse(status, headers or {}))


def response_with_retry_after(status: int, retry_after: str | None) -> aiohttp.ClientResponse:
    headers = {"Retry-After": retry_after} if retry_after else {}
    return fake_response(status, headers)


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
    ("status", "expected_error"),
    [(429, AoeClientRateLimitError), (503, AoeClientConnectionError)],
)
@pytest.mark.parametrize(
    ("retry_after_header", "retry_after_seconds"),
    [("30", 30), (None, None), ("Wed, 21 Oct 2026 07:28:00 GMT", None), ("²", None)],
)
def test_error_reads_retry_after(
    status: int,
    expected_error: type[AoeClientRateLimitError | AoeClientConnectionError],
    retry_after_header: str | None,
    retry_after_seconds: int | None,
):
    # Given
    response = response_with_retry_after(status, retry_after_header)

    # When
    with pytest.raises(expected_error) as raised:
        _raise_for_status(response)

    # Then
    assert raised.value.retry_after == retry_after_seconds


@pytest.mark.parametrize("status", [500, 502, 504])
def test_other_server_errors_ignore_retry_after(status: int):
    # Given
    response = response_with_retry_after(status, "30")

    # When
    with pytest.raises(AoeClientConnectionError) as raised:
        _raise_for_status(response)

    # Then
    assert raised.value.retry_after is None


async def test_requests_send_the_given_user_agent():
    # Given
    session = RecordingSession()

    # When
    await get_from(session)

    # Then
    assert session.sent_headers == [{"User-Agent": TEST_USER_AGENT}]


@pytest.mark.parametrize("policy", [BACKGROUND_REQUESTS, INTERACTIVE_REQUESTS])
async def test_requests_use_the_policy_timeout(policy: RequestPolicy):
    # Given
    session = RecordingSession()

    # When
    await get_from(session, policy)

    # Then
    assert session.sent_timeouts == [aiohttp.ClientTimeout(total=policy.timeout_seconds)]


@pytest.mark.parametrize("status", [429, 503])
@pytest.mark.usefixtures("no_backoff_sleep")
async def test_transient_errors_are_retried_until_success(status: int):
    # Given
    session = FlakySession(statuses=[status] * BACKGROUND_REQUESTS.max_retries)

    # When
    body = await get_from(session)

    # Then
    assert body == {"ok": True}
    assert session.attempts == BACKGROUND_REQUESTS.max_retries + 1


@pytest.mark.usefixtures("no_backoff_sleep")
async def test_interactive_requests_fail_on_first_server_error():
    # Given
    session = FlakySession(statuses=[503])

    # When
    with pytest.raises(AoeClientConnectionError):
        await get_from(session, INTERACTIVE_REQUESTS)

    # Then
    assert session.attempts == 1


@pytest.mark.parametrize(
    ("status", "expected_error"),
    [
        (404, AoeClientNotFoundError),
        (400, AoeClientResponseError),
    ],
)
@pytest.mark.usefixtures("no_backoff_sleep")
async def test_non_transient_failure_is_not_retried(status: int, expected_error: type[Exception]):
    # Given
    session = FlakySession(statuses=[status])

    # When
    with pytest.raises(expected_error):
        await get_from(session)

    # Then
    assert session.attempts == 1


async def test_rate_limited_request_waits_for_retry_after(monkeypatch: pytest.MonkeyPatch):
    # Given
    waits: list[float] = []

    async def record_sleep(delay: float) -> None:
        waits.append(delay)

    monkeypatch.setattr(_backoff.asyncio, "sleep", record_sleep)
    session = FlakySession(statuses=[429], headers={"Retry-After": "3"})

    # When
    body = await get_from(session)

    # Then
    assert body == {"ok": True}
    assert waits == [3]


@pytest.mark.parametrize(
    ("status", "expected_error"),
    [(429, AoeClientRateLimitError), (503, AoeClientConnectionError)],
)
@pytest.mark.usefixtures("no_backoff_sleep")
async def test_long_retry_after_is_left_to_the_caller(
    status: int, expected_error: type[AoeClientRateLimitError | AoeClientConnectionError]
):
    # Given
    retry_after = LONGEST_RETRY_WAIT_SECONDS + 1
    session = FlakySession(statuses=[status], headers={"Retry-After": str(retry_after)})

    # When
    with pytest.raises(expected_error) as raised:
        await get_from(session)

    # Then
    assert session.attempts == 1
    assert raised.value.retry_after == retry_after
