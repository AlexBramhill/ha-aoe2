from typing import Any

from custom_components.aoe2.models import MatchResult, PlayerData


def get_last_match_result(data: PlayerData) -> MatchResult | None:
    result = data.last_match_result()
    return None if result is MatchResult.UNKNOWN else result


def get_last_match_details(data: PlayerData) -> dict[str, Any]:
    match = data.last_finished_match()
    if match is None:
        return {}
    player = data.own_player_in(match)
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
