from datetime import datetime

from custom_components.aoe2.models import Match, MatchPlayer, MatchResult, PlayerData

type AttributeValue = str | int | float | datetime | list[str] | None
type StateAttributes = dict[str, AttributeValue]


def get_known_result(player: MatchPlayer) -> MatchResult | None:
    return None if player.result is MatchResult.UNKNOWN else player.result


def get_last_match_details(match: Match, player: MatchPlayer) -> StateAttributes:
    return {
        "leaderboard": match.leaderboard,
        "map": match.map_name,
        "civ": player.civ,
        "rating_after_match": player.rating_after_match,
        "teammates": [teammate.name for teammate in match.get_teammates_of(player)],
        "opponents": [opponent.name for opponent in match.get_opponents_of(player)],
    }


def get_current_match_details(data: PlayerData) -> StateAttributes:
    match = data.get_current_match()
    if match is None:
        return {}
    return {"leaderboard": match.leaderboard, "map": match.map_name, "started": match.started}


def get_percentage(fraction: float | None) -> float | None:
    return None if fraction is None else fraction * 100
