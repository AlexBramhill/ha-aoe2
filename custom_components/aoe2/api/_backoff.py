import asyncio
import math
import random
from collections.abc import Awaitable, Callable


async def with_exponential_backoff[T, E: Exception](
    request: Callable[[], Awaitable[T]],
    *,
    retry_on: type[E],
    max_retries: int,
    first_delay_seconds: float,
    get_requested_delay: Callable[[E], float | None] = lambda _: None,
    longest_wait_seconds: float = math.inf,
) -> T:
    for retry in range(max_retries):
        try:
            return await request()
        except retry_on as error:
            delay = _get_delay_before_retry(retry, first_delay_seconds, get_requested_delay(error))
            if delay > longest_wait_seconds:
                raise
            await asyncio.sleep(delay)
    return await request()


def _get_delay_before_retry(
    retry: int, first_delay_seconds: float, requested_delay: float | None
) -> float:
    if requested_delay is not None:
        return requested_delay
    return _get_exponential_delay(retry, first_delay_seconds) * _get_jitter()


def _get_exponential_delay(retry: int, first_delay_seconds: float) -> float:
    return first_delay_seconds * 2**retry


def _get_jitter() -> float:
    return random.uniform(1, 2)
