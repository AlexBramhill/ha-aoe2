from dataclasses import dataclass

from custom_components.aoe2.models import Leaderboard, Match


@dataclass(frozen=True, slots=True)
class MatchFinishedEvent:
    profile_id: int
    match_id: int
    leaderboard: Leaderboard
    map_name: str
    won: bool | None
    rating_after_match: int | None
    rating_change: int | None


def get_match_finished_event(match: Match, profile_id: int) -> MatchFinishedEvent:
    player = match.get_player_with_id(profile_id)
    return MatchFinishedEvent(
        profile_id=profile_id,
        match_id=match.match_id,
        leaderboard=match.leaderboard,
        map_name=match.map_name,
        won=player.is_winner,
        rating_after_match=player.rating_after_match,
        rating_change=player.rating_change,
    )
