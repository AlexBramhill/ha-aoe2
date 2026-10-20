from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Self

from custom_components.aoe2.api import Leaderboard, Profile, Rating
from custom_components.aoe2.api._worldsedge import LEADERBOARD_IDS

type Body = dict[str, Any]

WORLDSEDGE_IDS_BY_LEADERBOARD = {leaderboard: id_ for id_, leaderboard in LEADERBOARD_IDS.items()}
WORLDSEDGE_NO_RANK = -1
WORLDSEDGE_NO_HIGHEST_RATING = 0
WORLDSEDGE_NO_DATE = 0


@dataclass(frozen=True)
class ProfileBuilder:
    profile_id: int = 1
    name: str = "Player"
    country: str | None = None
    worldsedge_statgroup_id: int | None = None
    ratings: tuple[Rating, ...] = ()

    def with_name(self, name: str) -> Self:
        return replace(self, name=name)

    def with_country(self, country: str) -> Self:
        return replace(self, country=country)

    def with_worldsedge_statgroup_id(self, statgroup_id: int) -> Self:
        return replace(self, worldsedge_statgroup_id=statgroup_id)

    def with_rating(self, rating: Rating) -> Self:
        return replace(self, ratings=(*self.ratings, rating))

    def expected_profile(self) -> Profile:
        return Profile(
            profile_id=self.profile_id,
            name=self.name,
            country=self.country,
            ratings=self.ratings,
        )

    def aoe2companion_response(self) -> Body:
        return {
            "profileId": self.profile_id,
            "name": self.name,
            "country": self.country,
            "leaderboards": [_aoe2companion_leaderboard(rating) for rating in self.ratings],
        }

    def worldsedge_response(self) -> Body:
        return {
            "result": {"code": 0, "message": "SUCCESS"},
            "statGroups": [self._worldsedge_stat_group()],
            "leaderboardStats": [self._worldsedge_stat(rating) for rating in self.ratings],
        }

    @property
    def _statgroup_id(self) -> int:
        if self.worldsedge_statgroup_id is None:
            return self.profile_id
        return self.worldsedge_statgroup_id

    def _worldsedge_stat_group(self) -> Body:
        return {"id": self._statgroup_id, "members": [self._worldsedge_member()]}

    def _worldsedge_member(self) -> Body:
        return {
            "profile_id": self.profile_id,
            "alias": self.name,
            "personal_statgroup_id": self._statgroup_id,
            "country": self.country,
        }

    def _worldsedge_stat(self, rating: Rating) -> Body:
        return {
            "statgroup_id": self._statgroup_id,
            "leaderboard_id": _worldsedge_leaderboard_id(rating.leaderboard),
            "rating": rating.rating,
            "rank": rating.rank or WORLDSEDGE_NO_RANK,
            "wins": rating.wins,
            "losses": rating.losses,
            "streak": rating.streak,
            "highestrating": rating.highest_rating or WORLDSEDGE_NO_HIGHEST_RATING,
            "lastmatchdate": _epoch_seconds(rating.last_match),
        }


def build_rating(leaderboard: Leaderboard, rating: int, **fields: Any) -> Rating:
    unranked_with_no_games = Rating(
        leaderboard=leaderboard, rating=rating, rank=None, wins=0, losses=0, streak=0
    )
    return replace(unranked_with_no_games, **fields)


def _aoe2companion_leaderboard(rating: Rating) -> Body:
    return {
        "leaderboardId": rating.leaderboard.value,
        "rating": rating.rating,
        "rank": rating.rank,
        "wins": rating.wins,
        "losses": rating.losses,
        "streak": rating.streak,
        "maxRating": rating.highest_rating,
        "lastMatchTime": _iso_timestamp(rating.last_match),
    }


def _worldsedge_leaderboard_id(leaderboard: Leaderboard) -> int:
    if leaderboard not in WORLDSEDGE_IDS_BY_LEADERBOARD:
        raise ValueError(f"World's Edge has no {leaderboard} leaderboard")
    return WORLDSEDGE_IDS_BY_LEADERBOARD[leaderboard]


def _iso_timestamp(moment: datetime | None) -> str | None:
    return moment.strftime("%Y-%m-%dT%H:%M:%S.000Z") if moment else None


def _epoch_seconds(moment: datetime | None) -> int:
    return int(moment.timestamp()) if moment else WORLDSEDGE_NO_DATE
