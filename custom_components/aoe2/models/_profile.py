from dataclasses import dataclass
from datetime import datetime

from custom_components.aoe2.models._leaderboard import Leaderboard


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
