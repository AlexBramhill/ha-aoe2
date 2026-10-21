from collections.abc import Callable, Iterable
from dataclasses import replace
from functools import wraps

from .errors import AoeClientResponseError
from .models import MatchPlayer


def response_parser[**Params, Result](
    parse: Callable[Params, Result],
) -> Callable[Params, Result]:
    @wraps(parse)
    def parse_or_raise(*args: Params.args, **kwargs: Params.kwargs) -> Result:
        try:
            return parse(*args, **kwargs)
        except (KeyError, TypeError, ValueError) as error:
            raise AoeClientResponseError(f"Unexpected response shape: {error!r}") from error

    return parse_or_raise


def number_teams_from_one(players: Iterable[MatchPlayer]) -> tuple[MatchPlayer, ...]:
    players = tuple(players)
    source_teams = sorted({player.team for player in players})
    team_numbers = {team: number for number, team in enumerate(source_teams, start=1)}
    return tuple(replace(player, team=team_numbers[player.team]) for player in players)
