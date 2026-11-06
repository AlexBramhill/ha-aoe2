from collections.abc import Iterator
from typing import final

import aiohttp
from pydantic import BaseModel

from custom_components.aoe2.api._aoe2companion_responses import (
    MatchesResponse,
    MatchResponse,
    PlayerResponse,
    ProfileResponse,
    RatingResponse,
)
from custom_components.aoe2.api._http import BACKGROUND_REQUESTS, RequestPolicy, get_response
from custom_components.aoe2.models import Leaderboard, Match, MatchPlayer, Profile, Rating

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


@final
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
        response = await self._get_api_response(f"profiles/{profile_id}", ProfileResponse)
        return get_profile_from(response)

    async def get_recent_matches(self, profile_id: int, count: int = 5) -> list[Match]:
        response = await self._get_api_response(
            "matches", MatchesResponse, profile_ids=profile_id, per_page=count
        )
        return get_matches_from(response)

    async def _get_api_response[Response: BaseModel](
        self, path: str, response_type: type[Response], **params: str | int
    ) -> Response:
        return await get_response(
            self._session,
            f"{BASE_URL}/{path}",
            response_type,
            params,
            version=self._version,
            policy=self._policy,
        )


def get_profile_from(response: ProfileResponse) -> Profile:
    return Profile(
        profile_id=response.profile_id,
        name=response.name,
        country=response.country,
        ratings=tuple(_get_ratings_on_known_leaderboards(response)),
    )


def get_matches_from(response: MatchesResponse) -> list[Match]:
    return [_get_match(match) for match in response.matches]


def _get_ratings_on_known_leaderboards(response: ProfileResponse) -> Iterator[Rating]:
    """Unrecognised leaderboards are skipped: several would all collapse into OTHER."""
    for rating in response.leaderboards:
        if (leaderboard := _get_leaderboard(rating.leaderboard_id)) is not Leaderboard.OTHER:
            yield _get_rating(leaderboard, rating)


def _get_rating(leaderboard: Leaderboard, rating: RatingResponse) -> Rating:
    return Rating(
        leaderboard=leaderboard,
        rating=rating.rating,
        rank=rating.rank,
        wins=rating.wins,
        losses=rating.losses,
        streak=rating.streak,
        highest_rating=rating.max_rating,
        last_match=rating.last_match_time,
    )


def _get_match(match: MatchResponse) -> Match:
    return Match(
        match_id=match.match_id,
        started=match.started,
        finished=match.finished,
        leaderboard=_get_leaderboard(match.leaderboard_id),
        map_name=match.map_name,
        players=tuple(_get_match_player(player) for team in match.teams for player in team.players),
    )


def _get_match_player(player: PlayerResponse) -> MatchPlayer:
    return MatchPlayer(
        profile_id=player.profile_id,
        name=player.name,
        team=player.team,
        civ=player.civ_name,
        rating_after_match=_get_rating_after_match(player),
        rating_change=player.rating_diff,
        is_winner=player.won,
    )


def _get_rating_after_match(player: PlayerResponse) -> int | None:
    """aoe2companion reports the rating going into the match."""
    if player.rating is None or player.rating_diff is None:
        return None
    return player.rating + player.rating_diff


def _get_leaderboard(leaderboard_id: str) -> Leaderboard:
    """Leaderboards aoe2companion adds later become OTHER rather than an error."""
    return LEADERBOARDS_BY_ID.get(leaderboard_id, Leaderboard.OTHER)
