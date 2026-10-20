from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class Leaderboard(StrEnum):
    RM_1V1 = "rm_1v1"
    RM_TEAM = "rm_team"
    EW_1V1 = "ew_1v1"
    EW_TEAM = "ew_team"
    UNRANKED = "unranked"


@dataclass(frozen=True, slots=True)
class PlayerSummary:
    profile_id: int
    name: str
    country: str | None = None
    games: int | None = None


@dataclass(frozen=True, slots=True)
class Rating:
    leaderboard: Leaderboard
    rating: int
    rank: int | None
    wins: int
    losses: int
    streak: int
    highest_rating: int | None = None
    last_match: datetime | None = None

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
    name: str | None
    team: int | None
    civ: str | None
    rating: int | None
    rating_change: int | None
    won: bool | None


@dataclass(frozen=True, slots=True)
class Match:
    match_id: int
    started: datetime
    finished: datetime | None
    leaderboard: Leaderboard | None
    map_name: str | None
    players: tuple[MatchPlayer, ...]

    def player_with_id(self, profile_id: int) -> MatchPlayer | None:
        return next((player for player in self.players if player.profile_id == profile_id), None)
