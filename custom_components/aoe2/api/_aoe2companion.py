from collections.abc import Iterator
from datetime import datetime
from typing import Any

import aiohttp

from custom_components.aoe2.api._http import BACKGROUND_REQUESTS, RequestPolicy, get_json
from custom_components.aoe2.api._parsing import number_teams_from_one, response_parser
from custom_components.aoe2.api.models import Leaderboard, Match, MatchPlayer, Profile, Rating

BASE_URL = "https://data.aoe2companion.com/api"
WEBSITE_URL = "https://www.aoe2companion.com"
PROFILE_URL = f"{WEBSITE_URL}/profile/{{profile_id}}"
ATTRIBUTION = "Data provided by aoe2companion.com"

LEADERBOARDS_BY_ID: dict[str, Leaderboard] = {
    "rm_1v1": Leaderboard.RM_1V1,
    "rm_team": Leaderboard.RM_TEAM,
    "ew_1v1": Leaderboard.EW_1V1,
    "ew_team": Leaderboard.EW_TEAM,
    "qp_rm_1v1": Leaderboard.QP_RM_1V1,
    "qp_rm_team": Leaderboard.QP_RM_TEAM,
    "dm_1v1": Leaderboard.DM_1V1,
    "dm_team": Leaderboard.DM_TEAM,
    "unranked": Leaderboard.UNRANKED,
    "rm_1v1_console": Leaderboard.RM_1V1_CONSOLE,
    "rm_team_console": Leaderboard.RM_TEAM_CONSOLE,
    "ew_1v1_console": Leaderboard.EW_1V1_CONSOLE,
    "ew_team_console": Leaderboard.EW_TEAM_CONSOLE,
}


class Aoe2CompanionClient:
    def __init__(
        self,
        session: aiohttp.ClientSession,
        version: str,
        policy: RequestPolicy = BACKGROUND_REQUESTS,
    ) -> None:
        self._session = session
        self._version = version
        self._policy = policy

    @property
    def attribution(self) -> str:
        return ATTRIBUTION

    @property
    def website_url(self) -> str:
        return WEBSITE_URL

    def profile_url(self, profile_id: int) -> str:
        return PROFILE_URL.format(profile_id=profile_id)

    async def get_profile(self, profile_id: int) -> Profile:
        body = await self._get(f"profiles/{profile_id}")
        return parse_profile(body)

    async def get_recent_matches(self, profile_id: int, count: int = 5) -> list[Match]:
        body = await self._get("matches", profile_ids=profile_id, per_page=count)
        return parse_matches(body)

    async def _get(self, path: str, **params: Any) -> dict[str, Any]:
        return await get_json(
            self._session,
            f"{BASE_URL}/{path}",
            params,
            version=self._version,
            policy=self._policy,
        )


@response_parser
def parse_profile(body: dict[str, Any]) -> Profile:
    return Profile(
        profile_id=body["profileId"],
        name=body["name"],
        country=body.get("country"),
        ratings=tuple(_get_known_ratings(body)),
    )


@response_parser
def parse_matches(body: dict[str, Any]) -> list[Match]:
    return [_get_match(match) for match in body.get("matches", [])]


def _get_known_ratings(body: dict[str, Any]) -> Iterator[Rating]:
    """Unrecognised leaderboards are skipped: several would all collapse into OTHER."""
    for raw in body.get("leaderboards", []):
        if (leaderboard := _get_leaderboard(raw["leaderboardId"])) is not Leaderboard.OTHER:
            yield _get_rating(leaderboard, raw)


def _get_rating(leaderboard: Leaderboard, raw: dict[str, Any]) -> Rating:
    return Rating(
        leaderboard=leaderboard,
        rating=raw["rating"],
        rank=raw.get("rank"),
        wins=raw.get("wins", 0),
        losses=raw.get("losses", 0),
        streak=raw.get("streak", 0),
        highest_rating=raw["maxRating"],
        last_match=datetime.fromisoformat(raw["lastMatchTime"]),
    )


def _get_match(raw: dict[str, Any]) -> Match:
    return Match(
        match_id=raw["matchId"],
        started=datetime.fromisoformat(raw["started"]),
        finished=_get_datetime_or_none(raw.get("finished")),
        leaderboard=_get_leaderboard(raw["leaderboardId"]),
        map_name=raw["mapName"],
        players=number_teams_from_one(
            _get_match_player(player) for player in _get_all_players(raw)
        ),
    )


def _get_all_players(match: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for team in match.get("teams", []):
        yield from team.get("players", [])


def _get_match_player(raw: dict[str, Any]) -> MatchPlayer:
    return MatchPlayer(
        profile_id=raw["profileId"],
        name=raw["name"],
        team=raw["team"],
        civ=raw["civName"],
        rating_after_match=_get_rating_after_match(raw),
        rating_change=raw.get("ratingDiff"),
        won=raw.get("won"),
    )


def _get_rating_after_match(raw: dict[str, Any]) -> int | None:
    """aoe2companion reports the rating going into the match."""
    rating_before, change = raw.get("rating"), raw.get("ratingDiff")
    if rating_before is None or change is None:
        return None
    return rating_before + change


def _get_datetime_or_none(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def _get_leaderboard(leaderboard_id: str) -> Leaderboard:
    """Leaderboards aoe2companion adds later become OTHER rather than an error."""
    return LEADERBOARDS_BY_ID.get(leaderboard_id, Leaderboard.OTHER)
