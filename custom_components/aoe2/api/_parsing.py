from collections.abc import Callable
from functools import wraps

from .errors import AoeClientResponseError


def response_parser[**P, R](parse: Callable[P, R]) -> Callable[P, R]:
    @wraps(parse)
    def parse_or_raise(*args: P.args, **kwargs: P.kwargs) -> R:
        try:
            return parse(*args, **kwargs)
        except (KeyError, TypeError, ValueError) as err:
            raise AoeClientResponseError(f"Unexpected response shape: {err!r}") from err

    return parse_or_raise
