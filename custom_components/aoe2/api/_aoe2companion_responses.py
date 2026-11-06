from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class _Response(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(
        alias_generator=to_camel, validate_by_name=True, strict=True, frozen=True
    )


class RatingResponse(_Response):
    leaderboard_id: str
    rating: int
    rank: int | None = None
    wins: int = 0
    losses: int = 0
    streak: int = 0
    max_rating: int
    last_match_time: datetime


class ProfileResponse(_Response):
    profile_id: int
    name: str
    country: str | None = None
    leaderboards: list[RatingResponse] = []


class PlayerResponse(_Response):
    profile_id: int
    name: str
    team: int
    civ_name: str
    rating: int | None = None
    rating_diff: int | None = None
    won: bool | None = None


class TeamResponse(_Response):
    players: list[PlayerResponse] = []


class MatchResponse(_Response):
    match_id: int
    started: datetime
    finished: datetime | None = None
    leaderboard_id: str
    map_name: str
    teams: list[TeamResponse] = []


class MatchesResponse(_Response):
    matches: list[MatchResponse] = []
