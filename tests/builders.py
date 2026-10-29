from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from typing import Any, Self

from custom_components.aoe2.models import Leaderboard, Match, MatchPlayer, Profile, Rating
from tests.api.api_json import (
    Body,
    aoe2companion_matches_json,
    aoe2companion_profile_json,
)


@dataclass(frozen=True)
class BuiltProfile:
    expected: Profile
    aoe2companion_response: Body


@dataclass(frozen=True)
class BuiltMatchHistory:
    expected: list[Match]
    aoe2companion_response: Body


TYPICAL_LAST_MATCH = datetime(2026, 10, 1, 18, 30, tzinfo=UTC)


def build_rating(leaderboard: Leaderboard, rating: int, **fields: Any) -> Rating:
    unranked_with_one_game = Rating(
        leaderboard=leaderboard,
        rating=rating,
        rank=None,
        wins=1,
        losses=0,
        streak=1,
        highest_rating=rating,
        last_match=TYPICAL_LAST_MATCH,
    )
    return replace(unranked_with_one_game, **fields)


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
        ratings = _replace_or_append(self.ratings, rating, key=lambda item: item.leaderboard)
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
        )


def build_match_player(profile_id: int, **fields: Any) -> MatchPlayer:
    winner_on_team_one = MatchPlayer(
        profile_id=profile_id,
        name=f"Player {profile_id}",
        team=1,
        civ="Franks",
        rating_after_match=1510,
        rating_change=10,
        is_winner=True,
    )
    return replace(winner_on_team_one, **fields)


TYPICAL_PLAYERS = (
    build_match_player(1),
    build_match_player(2, team=2, rating_after_match=1490, rating_change=-10, is_winner=False),
)
TYPICAL_START = datetime(2026, 10, 1, 18, 0, tzinfo=UTC)
TYPICAL_DURATION = timedelta(minutes=35)


@dataclass(frozen=True)
class MatchBuilder:
    match_id: int = 1
    started: datetime = TYPICAL_START
    finished: datetime | None = TYPICAL_START + TYPICAL_DURATION
    leaderboard: Leaderboard = Leaderboard.RM_1V1
    map_name: str = "Arabia"
    players: tuple[MatchPlayer, ...] = TYPICAL_PLAYERS

    def with_match_id(self, match_id: int) -> Self:
        return replace(self, match_id=match_id)

    def with_start(self, started: datetime) -> Self:
        return replace(self, started=started, finished=started + TYPICAL_DURATION)

    def unfinished(self) -> Self:
        return replace(self, finished=None)

    def with_leaderboard(self, leaderboard: Leaderboard) -> Self:
        return replace(self, leaderboard=leaderboard)

    def with_map_name(self, map_name: str) -> Self:
        return replace(self, map_name=map_name)

    def with_player(self, player: MatchPlayer) -> Self:
        players = _replace_or_append(self.players, player, key=lambda item: item.profile_id)
        return replace(self, players=players)

    def build(self) -> Match:
        return Match(
            match_id=self.match_id,
            started=self.started,
            finished=self.finished,
            leaderboard=self.leaderboard,
            map_name=self.map_name,
            players=tuple(sorted(self.players, key=_team_order)),
        )


def build_match_history(*matches: MatchBuilder) -> BuiltMatchHistory:
    expected = [match.build() for match in matches]
    return BuiltMatchHistory(
        expected=expected,
        aoe2companion_response=aoe2companion_matches_json(expected),
    )


def _replace_or_append[Item](
    items: tuple[Item, ...], new_item: Item, key: Callable[[Item], object]
) -> tuple[Item, ...]:
    if all(key(existing) != key(new_item) for existing in items):
        return (*items, new_item)
    return tuple(new_item if key(existing) == key(new_item) else existing for existing in items)


def _team_order(player: MatchPlayer) -> int:
    return player.team
