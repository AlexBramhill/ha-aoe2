import asyncio
import random
from collections.abc import Awaitable, Callable
from contextlib import suppress


async def with_exponential_backoff[T](
    request: Callable[[], Awaitable[T]],
    *,
    retry_on: type[Exception],
    max_retries: int,
    first_delay_seconds: float,
) -> T:
    for retry in range(max_retries):
        with suppress(retry_on):
            return await request()
        await asyncio.sleep(_backoff_delay(retry, first_delay_seconds))
    return await request()


def _backoff_delay(retry: int, first_delay_seconds: float) -> float:
    return _exponential_delay(retry, first_delay_seconds) * _jitter()


def _exponential_delay(retry: int, first_delay_seconds: float) -> float:
    return first_delay_seconds * 2**retry


def _jitter() -> float:
    return random.uniform(1, 2)
