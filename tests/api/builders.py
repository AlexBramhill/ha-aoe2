from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import Any, Self

from custom_components.aoe2.api import Leaderboard, Profile, Rating
from tests.api.api_json import Body, aoe2companion_profile_json, worldsedge_profile_json


@dataclass(frozen=True)
class BuiltProfile:
    expected: Profile
    aoe2companion_response: Body
    worldsedge_response: Body


def build_rating(leaderboard: Leaderboard, rating: int, **fields: Any) -> Rating:
    unranked_with_no_games = Rating(
        leaderboard=leaderboard, rating=rating, rank=None, wins=0, losses=0, streak=0
    )
    return replace(unranked_with_no_games, **fields)


TYPICAL_RATINGS = (
    build_rating(
        Leaderboard.RM_1V1,
        1650,
        rank=4200,
        wins=310,
        losses=290,
        streak=2,
        highest_rating=1712,
        last_match=datetime(2026, 10, 1, 18, 30, tzinfo=UTC),
    ),
    build_rating(
        Leaderboard.RM_TEAM,
        1580,
        rank=9100,
        wins=120,
        losses=95,
        streak=-1,
        highest_rating=1644,
        last_match=datetime(2026, 9, 28, 20, 15, tzinfo=UTC),
    ),
)


@dataclass(frozen=True)
class ProfileBuilder:
    profile_id: int = 1
    name: str = "Player"
    country: str | None = "gb"
    ratings: tuple[Rating, ...] = TYPICAL_RATINGS

    def with_profile_id(self, profile_id: int) -> Self:
        return replace(self, profile_id=profile_id)

    def with_name(self, name: str) -> Self:
        return replace(self, name=name)

    def with_country(self, country: str | None) -> Self:
        return replace(self, country=country)

    def with_rating(self, rating: Rating) -> Self:
        if all(existing.leaderboard != rating.leaderboard for existing in self.ratings):
            return replace(self, ratings=(*self.ratings, rating))
        ratings = tuple(
            rating if existing.leaderboard == rating.leaderboard else existing
            for existing in self.ratings
        )
        return replace(self, ratings=ratings)

    def without_ratings(self) -> Self:
        return replace(self, ratings=())

    def build(self) -> BuiltProfile:
        profile = Profile(
            profile_id=self.profile_id,
            name=self.name,
            country=self.country,
            ratings=self.ratings,
        )
        return BuiltProfile(
            expected=profile,
            aoe2companion_response=aoe2companion_profile_json(profile),
            worldsedge_response=worldsedge_profile_json(profile),
        )
