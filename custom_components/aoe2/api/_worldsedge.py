import json
import re
from collections.abc import Iterator
from datetime import UTC, datetime
from typing import Any

import aiohttp

from ._http import get_json
from ._parsing import response_parser
from .errors import AoeClientNotFoundError, AoeClientResponseError
from .models import Leaderboard, Match, MatchPlayer, Profile, Rating

BASE_URL = "https://aoe-api.worldsedgelink.com/community/leaderboard"
TITLE = "age2"

RESULT_OK = 0
RESULT_UNKNOWN_PROFILE = 6

LEADERBOARD_IDS: dict[int, Leaderboard] = {
    3: Leaderboard.RM_1V1,
    4: Leaderboard.RM_TEAM,
    13: Leaderboard.EW_1V1,
    14: Leaderboard.EW_TEAM,
}

MATCH_TYPES: dict[int, Leaderboard] = {
    0: Leaderboard.UNRANKED,
    6: Leaderboard.RM_1V1,
    7: Leaderboard.RM_TEAM,
    8: Leaderboard.RM_TEAM,
    9: Leaderboard.RM_TEAM,
    26: Leaderboard.EW_1V1,
    27: Leaderboard.EW_TEAM,
    28: Leaderboard.EW_TEAM,
    29: Leaderboard.EW_TEAM,
}


class WorldsEdgeClient:
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session

    async def get_profile(self, profile_id: int) -> Profile:
        body = await self._get("GetPersonalStat", profile_ids=_json_list(profile_id))
        return parse_profile(body, profile_id)

    async def get_recent_matches(self, profile_id: int, count: int = 5) -> list[Match]:
        body = await self._get("getRecentMatchHistory", profile_ids=_json_list(profile_id))
        return parse_matches(body)[:count]

    async def _get(self, endpoint: str, **params: Any) -> dict[str, Any]:
        url = f"{BASE_URL}/{endpoint}"
        body = await get_json(self._session, url, {"title": TITLE, **params})
        _raise_for_result(body)
        return body


def _json_list(value: Any) -> str:
    return json.dumps([value])


def _raise_for_result(body: dict[str, Any]) -> None:
    """World's Edge reports errors as a result code inside an HTTP 200 body."""
    result = body.get("result", {})
    code = result.get("code")
    if code == RESULT_OK:
        return
    if code == RESULT_UNKNOWN_PROFILE:
        raise AoeClientNotFoundError(result.get("message"))
    raise AoeClientResponseError(f"World's Edge error: {result}")


@response_parser
def parse_profile(body: dict[str, Any], profile_id: int) -> Profile:
    member = _find_member(body, profile_id)
    return Profile(
        profile_id=profile_id,
        name=member["alias"],
        country=member.get("country"),
        ratings=tuple(_known_ratings(body, member["personal_statgroup_id"])),
    )


@response_parser
def parse_matches(body: dict[str, Any]) -> list[Match]:
    names = _player_names(body)
    matches = [_match(match, names) for match in body.get("matchHistoryStats", [])]
    return _newest_first(matches)


def pretty_map_name(filename: str | None) -> str | None:
    """'CoastalForest.rms' -> 'Coastal Forest'; custom names pass through."""
    if not filename:
        return None
    stem = re.sub(r"\.rms2?$", "", filename)
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", stem).replace("_", " ").strip()


def _all_members(body: dict[str, Any]) -> Iterator[dict[str, Any]]:
    for group in body.get("statGroups", []):
        yield from group.get("members", [])


def _find_member(body: dict[str, Any], profile_id: int) -> dict[str, Any]:
    for member in _all_members(body):
        if member["profile_id"] == profile_id:
            return member
    raise AoeClientNotFoundError(profile_id)


def _known_ratings(body: dict[str, Any], statgroup_id: int) -> Iterator[Rating]:
    for raw in body.get("leaderboardStats", []):
        if raw.get("statgroup_id") != statgroup_id:
            continue
        if (leaderboard := LEADERBOARD_IDS.get(raw.get("leaderboard_id"))) is not None:
            yield _rating(leaderboard, raw)


def _rating(leaderboard: Leaderboard, raw: dict[str, Any]) -> Rating:
    return Rating(
        leaderboard=leaderboard,
        rating=raw["rating"],
        rank=_positive_or_none(raw.get("rank")),
        wins=raw.get("wins", 0),
        losses=raw.get("losses", 0),
        streak=raw.get("streak", 0),
        highest_rating=_positive_or_none(raw.get("highestrating")),
        last_match=_datetime_or_none(raw.get("lastmatchdate")),
    )


def _player_names(body: dict[str, Any]) -> dict[int, str]:
    return {profile["profile_id"]: profile["alias"] for profile in body.get("profiles", [])}


def _match(raw: dict[str, Any], names: dict[int, str]) -> Match:
    members = raw.get("matchhistorymember", [])
    return Match(
        match_id=raw["id"],
        started=datetime.fromtimestamp(raw["startgametime"], UTC),
        finished=_datetime_or_none(raw.get("completiontime")),
        leaderboard=MATCH_TYPES.get(raw.get("matchtype_id")),
        map_name=pretty_map_name(raw.get("mapname")),
        players=tuple(_match_player(member, names) for member in members),
    )


def _match_player(member: dict[str, Any], names: dict[int, str]) -> MatchPlayer:
    return MatchPlayer(
        profile_id=member["profile_id"],
        name=names.get(member["profile_id"]),
        team=member.get("teamid"),
        # Undocumented API. Civs come back as numeric IDs only,
        # so we set civ to none for the time being.
        civ=None,
        rating=member.get("newrating"),
        rating_change=_rating_change(member),
        won=_won(member),
    )


def _rating_change(member: dict[str, Any]) -> int | None:
    old, new = member.get("oldrating"), member.get("newrating")
    return new - old if old is not None and new is not None else None


def _won(member: dict[str, Any]) -> bool | None:
    return {1: True, 0: False}.get(member.get("outcome"))


def _newest_first(matches: list[Match]) -> list[Match]:
    """The API returns matches unordered."""
    return sorted(matches, key=lambda match: match.started, reverse=True)


def _positive_or_none(value: int | None) -> int | None:
    return value if value and value > 0 else None


def _datetime_or_none(epoch_seconds: int | None) -> datetime | None:
    return datetime.fromtimestamp(epoch_seconds, UTC) if epoch_seconds else None
