from collections.abc import Callable
from datetime import datetime
from typing import Any

from custom_components.aoe2.logic._match_result import MatchResult, get_match_result
from custom_components.aoe2.logic._player_data import PlayerData
from custom_components.aoe2.models import Match, MatchPlayer


def get_last_match_result(data: PlayerData) -> MatchResult | None:
    result = _get_from_last_match(data, lambda match: get_match_result(data.player_in(match).won))
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
        "teammates": _get_teammates(match, player),
        "opponents": _get_opponents(match, player),
    }


def get_current_match_details(data: PlayerData) -> dict[str, Any]:
    match = data.current_match()
    if match is None:
        return {}
    return {"leaderboard": match.leaderboard, "map": match.map_name, "started": match.started}


def get_recent_win_rate(data: PlayerData) -> float | None:
    results = [data.player_in(match).won for match in data.finished_matches()]
    known_results = [won for won in results if won is not None]
    if not known_results:
        return None
    return get_percentage(known_results.count(True) / len(known_results))


def get_recent_rating_change(data: PlayerData) -> int | None:
    changes = [data.player_in(match).rating_change for match in data.finished_matches()]
    known_changes = [change for change in changes if change is not None]
    return sum(known_changes) if known_changes else None


def get_percentage(fraction: float | None) -> float | None:
    return None if fraction is None else round(fraction * 100, 1)


def _get_from_last_match[Value](
    data: PlayerData, value_of: Callable[[Match], Value]
) -> Value | None:
    match = data.last_finished_match()
    return None if match is None else value_of(match)


def _get_teammates(match: Match, player: MatchPlayer) -> list[str]:
    return [
        other.name
        for other in match.players
        if other.team == player.team and other.profile_id != player.profile_id
    ]


def _get_opponents(match: Match, player: MatchPlayer) -> list[str]:
    return [other.name for other in match.players if other.team != player.team]
