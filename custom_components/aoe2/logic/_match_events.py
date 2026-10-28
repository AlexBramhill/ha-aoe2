from dataclasses import dataclass

from custom_components.aoe2.api import Leaderboard, Match, MatchPlayer


@dataclass(frozen=True, slots=True)
class PlayerResult:
    won: bool | None
    rating_after_match: int | None
    rating_change: int | None


@dataclass(frozen=True, slots=True)
class MatchFinishedEvent:
    profile_id: int
    match_id: int
    leaderboard: Leaderboard
    map_name: str
    result: PlayerResult


def get_match_finished_event(match: Match, profile_id: int) -> MatchFinishedEvent:
    return MatchFinishedEvent(
        profile_id=profile_id,
        match_id=match.match_id,
        leaderboard=match.leaderboard,
        map_name=match.map_name,
        result=_get_player_result(match.player_with_id(profile_id)),
    )


def _get_player_result(player: MatchPlayer) -> PlayerResult:
    return PlayerResult(
        won=player.won,
        rating_after_match=player.rating_after_match,
        rating_change=player.rating_change,
    )
