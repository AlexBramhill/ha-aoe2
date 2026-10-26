from dataclasses import dataclass

import pytest

from custom_components.aoe2.api import _backoff
from custom_components.aoe2.api._backoff import with_exponential_backoff

MAX_RETRIES = 3


class TransientError(Exception):
    pass


class PermanentError(Exception):
    pass


@dataclass
class FlakyRequest:
    """Raises the given error for the first few calls, then succeeds."""

    failures: int
    error: type[Exception] = TransientError
    calls: int = 0

    async def __call__(self) -> str:
        self.calls += 1
        if self.calls <= self.failures:
            raise self.error
        return "ok"


@pytest.fixture
def backoff_delays(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    delays: list[float] = []

    async def record_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(_backoff.asyncio, "sleep", record_sleep)
    return delays


async def run_with_backoff(request: FlakyRequest) -> str:
    return await with_exponential_backoff(
        request, retry_on=TransientError, max_retries=MAX_RETRIES, first_delay_seconds=1.0
    )


async def test_success_on_first_attempt_does_not_wait(backoff_delays: list[float]):
    # Given
    request = FlakyRequest(failures=0)

    # When
    result = await run_with_backoff(request)

    # Then
    assert result == "ok"
    assert request.calls == 1
    assert backoff_delays == []


async def test_retries_until_success(backoff_delays: list[float]):
    # Given
    request = FlakyRequest(failures=2)

    # When
    result = await run_with_backoff(request)

    # Then
    assert result == "ok"
    assert request.calls == 3
    assert len(backoff_delays) == 2


async def test_gives_up_after_max_retries(backoff_delays: list[float]):
    # Given
    request = FlakyRequest(failures=MAX_RETRIES + 1)

    # When
    with pytest.raises(TransientError):
        await run_with_backoff(request)

    # Then
    assert request.calls == MAX_RETRIES + 1


async def test_delays_double_with_jitter(backoff_delays: list[float]):
    # Given
    request = FlakyRequest(failures=MAX_RETRIES)

    # When
    await run_with_backoff(request)

    # Then
    assert 1 <= backoff_delays[0] <= 2
    assert 2 <= backoff_delays[1] <= 4
    assert 4 <= backoff_delays[2] <= 8


async def test_other_errors_are_not_retried(backoff_delays: list[float]):
    # Given
    request = FlakyRequest(failures=1, error=PermanentError)

    # When
    with pytest.raises(PermanentError):
        await run_with_backoff(request)

    # Then
    assert request.calls == 1
    assert backoff_delays == []
