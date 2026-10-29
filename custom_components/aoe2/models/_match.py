from dataclasses import dataclass
from datetime import datetime

from custom_components.aoe2.models._leaderboard import Leaderboard
from custom_components.aoe2.models._match_result import MatchResult


@dataclass(frozen=True, slots=True)
class MatchPlayer:
    profile_id: int
    name: str
    team: int
    civ: str
    rating_after_match: int | None
    rating_change: int | None
    is_winner: bool | None

    @property
    def result(self) -> MatchResult:
        return MatchResult.from_is_winner(self.is_winner)


@dataclass(frozen=True, slots=True)
class Match:
    match_id: int
    started: datetime
    finished: datetime | None
    leaderboard: Leaderboard
    map_name: str
    players: tuple[MatchPlayer, ...]

    @property
    def is_finished(self) -> bool:
        return self.finished is not None

    def get_player_with_id(self, profile_id: int) -> MatchPlayer:
        for player in self.players:
            if player.profile_id == profile_id:
                return player
        raise LookupError(f"Profile {profile_id} did not play in match {self.match_id}")

    def teammates_of(self, player: MatchPlayer) -> tuple[MatchPlayer, ...]:
        return tuple(
            other
            for other in self.players
            if other.team == player.team and other.profile_id != player.profile_id
        )

    def opponents_of(self, player: MatchPlayer) -> tuple[MatchPlayer, ...]:
        return tuple(other for other in self.players if other.team != player.team)
