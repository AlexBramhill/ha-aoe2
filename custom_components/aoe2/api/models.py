from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Leaderboard(StrEnum):
    RM_1V1 = "rm_1v1"
    RM_TEAM = "rm_team"
    EW_1V1 = "ew_1v1"
    EW_TEAM = "ew_team"
    QP_RM_1V1 = "qp_rm_1v1"
    QP_RM_TEAM = "qp_rm_team"
    DM_1V1 = "dm_1v1"
    DM_TEAM = "dm_team"
    UNRANKED = "unranked"
    RM_1V1_CONSOLE = "rm_1v1_console"
    RM_TEAM_CONSOLE = "rm_team_console"
    EW_1V1_CONSOLE = "ew_1v1_console"
    EW_TEAM_CONSOLE = "ew_team_console"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Rating:
    leaderboard: Leaderboard
    rating: int
    rank: int | None
    wins: int
    losses: int
    streak: int
    highest_rating: int
    last_match: datetime

    @property
    def games(self) -> int:
        return self.wins + self.losses

    @property
    def win_rate(self) -> float | None:
        return self.wins / self.games if self.games else None


@dataclass(frozen=True, slots=True)
class Profile:
    profile_id: int
    name: str
    country: str | None
    ratings: tuple[Rating, ...]

    def rating_for(self, leaderboard: Leaderboard) -> Rating | None:
        return next((rating for rating in self.ratings if rating.leaderboard == leaderboard), None)


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

    def player_with_id(self, profile_id: int) -> MatchPlayer:
        for player in self.players:
            if player.profile_id == profile_id:
                return player
        raise LookupError(f"Profile {profile_id} did not play in match {self.match_id}")
