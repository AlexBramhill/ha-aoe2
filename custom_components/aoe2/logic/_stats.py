from collections.abc import Callable
from datetime import datetime
from typing import Any

from custom_components.aoe2.models import Match, MatchResult, PlayerData


def get_last_match_result(data: PlayerData) -> MatchResult | None:
    result = _get_from_last_match(data, lambda match: data.player_in(match).result)
    return None if result is MatchResult.UNKNOWN else result


def get_last_match_rating_change(data: PlayerData) -> int | None:
    return _get_from_last_match(data, lambda match: data.player_in(match).rating_change)


def get_last_played(data: PlayerData) -> datetime | None:
    return _get_from_last_match(data, lambda match: match.finished)


def get_last_match_map(data: PlayerData) -> str | None:
    return _get_from_last_match(data, lambda match: match.map_name)


def get_last_match_civ(data: PlayerData) -> str | None:
    return _get_from_last_match(data, lambda match: data.player_in(match).civ)


def get_last_match_details(data: PlayerData) -> dict[str, Any]:
    match = data.last_finished_match()
    if match is None:
        return {}
    player = data.player_in(match)
    return {
        "leaderboard": match.leaderboard,
        "map": match.map_name,
        "civ": player.civ,
        "rating_after_match": player.rating_after_match,
        "teammates": [teammate.name for teammate in match.teammates_of(player)],
        "opponents": [opponent.name for opponent in match.opponents_of(player)],
    }


def get_current_match_details(data: PlayerData) -> dict[str, Any]:
    match = data.current_match()
    if match is None:
        return {}
    return {"leaderboard": match.leaderboard, "map": match.map_name, "started": match.started}


def get_percentage(fraction: float | None) -> float | None:
    return None if fraction is None else round(fraction * 100, 1)


def _get_from_last_match[Value](
    data: PlayerData, value_of: Callable[[Match], Value]
) -> Value | None:
    match = data.last_finished_match()
    return None if match is None else value_of(match)
