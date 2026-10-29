from dataclasses import dataclass
from datetime import datetime

from custom_components.aoe2.models._leaderboard import Leaderboard


@dataclass(frozen=True, slots=True)
class MatchPlayer:
    profile_id: int
    name: str
    team: int
    civ: str
    rating_after_match: int | None
    rating_change: int | None
    won: bool | None


@dataclass(frozen=True, slots=True)
class Match:
    match_id: int
    started: datetime
    finished: datetime | None
    leaderboard: Leaderboard
    map_name: str
    players: tuple[MatchPlayer, ...]

    def get_player_with_id(self, profile_id: int) -> MatchPlayer:
        for player in self.players:
            if player.profile_id == profile_id:
                return player
        raise LookupError(f"Profile {profile_id} did not play in match {self.match_id}")
