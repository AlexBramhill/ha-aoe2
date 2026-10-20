from collections.abc import Iterator
from datetime import datetime
from typing import Any

import aiohttp

from ._http import get_json
from ._parsing import response_parser
from .models import Leaderboard, Match, MatchPlayer, Profile, Rating

BASE_URL = "https://data.aoe2companion.com/api"


class Aoe2CompanionClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def get_profile(self, profile_id: int) -> Profile:
        body = await self._get(f"profiles/{profile_id}")
        return parse_profile(body)

    async def get_recent_matches(self, profile_id: int, count: int = 5) -> list[Match]:
        body = await self._get("matches", profile_ids=profile_id, per_page=count)
        return parse_matches(body)

    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        return await get_json(self._session, f"{BASE_URL}/{path}", params)


@response_parser
def parse_profile(body: dict[str, Any]) -> Profile:
    return Profile(
        profile_id=body["profileId"],
        name=body["name"],
        country=body.get("country"),
        ratings=tuple(_known_ratings(body)),
    )


@response_parser
def parse_matches(body: dict[str, Any]) -> list[Match]:
    return [_match(match) for match in body.get("matches", [])]


def _known_ratings(profile: dict[str, Any]) -> Iterator[Rating]:
    for raw in profile.get("leaderboards", []):
        if (leaderboard := _leaderboard_or_none(raw.get("leaderboardId"))) is not None:
            yield _rating(leaderboard, raw)


def _rating(leaderboard: Leaderboard, raw: dict[str, Any]) -> Rating:
    return Rating(
        leaderboard=leaderboard,
        rating=raw["rating"],
        rank=raw.get("rank"),
        wins=raw.get("wins", 0),
        losses=raw.get("losses", 0),
        streak=raw.get("streak", 0),
        highest_rating=raw.get("maxRating"),
        last_match=_datetime_or_none(raw.get("lastMatchTime")),
    )


def _match(raw: dict[str, Any]) -> Match:
    return Match(
        match_id=raw["matchId"],
        started=datetime.fromisoformat(raw["started"]),
        finished=_datetime_or_none(raw.get("finished")),
        leaderboard=_leaderboard_or_none(raw.get("leaderboardId")),
        map_name=raw.get("mapName"),
        players=tuple(_match_player(player) for player in _all_players(raw)),
    )


def _all_players(match: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for team in match.get("teams", []):
        yield from team.get("players", [])


def _match_player(raw: dict[str, Any]) -> MatchPlayer:
    return MatchPlayer(
        profile_id=raw["profileId"],
        name=raw.get("name"),
        team=raw.get("team"),
        civ=raw.get("civName"),
        rating_after_match=_rating_after_match(raw),
        rating_change=raw.get("ratingDiff"),
        won=raw.get("won"),
    )


def _rating_after_match(raw: dict[str, Any]) -> int | None:
    """aoe2companion reports the rating going into the match."""
    rating_before, change = raw.get("rating"), raw.get("ratingDiff")
    if rating_before is None or change is None:
        return rating_before
    return rating_before + change


def _leaderboard_or_none(value: str | None) -> Leaderboard | None:
    try:
        return Leaderboard(value)
    except ValueError:
        return None


def _datetime_or_none(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None
