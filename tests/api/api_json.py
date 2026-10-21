from datetime import datetime
from itertools import groupby
from typing import Any

from custom_components.aoe2.api import Leaderboard, Match, MatchPlayer, Profile, Rating
from custom_components.aoe2.api._worldsedge import (
    LEADERBOARD_IDS,
    MATCH_TYPES,
    OUTCOME_LOSS,
    OUTCOME_WIN,
)

type Body = dict[str, Any]

WORLDSEDGE_IDS_BY_LEADERBOARD = {
    leaderboard: leaderboard_id for leaderboard_id, leaderboard in LEADERBOARD_IDS.items()
}
WORLDSEDGE_MATCH_TYPES_BY_LEADERBOARD = {
    leaderboard: match_type for match_type, leaderboard in reversed(MATCH_TYPES.items())
}
WORLDSEDGE_UNKNOWN_CIV = 0
WORLDSEDGE_NO_RANK = -1
WORLDSEDGE_NO_HIGHEST_RATING = 0
WORLDSEDGE_NO_DATE = 0


def aoe2companion_profile_json(profile: Profile) -> Body:
    return {
        "profileId": profile.profile_id,
        "name": profile.name,
        "country": profile.country,
        "leaderboards": [_aoe2companion_leaderboard(rating) for rating in profile.ratings],
    }


def worldsedge_profile_json(profile: Profile) -> Body:
    statgroup_id = profile.profile_id
    member = {
        "profile_id": profile.profile_id,
        "alias": profile.name,
        "personal_statgroup_id": statgroup_id,
        "country": profile.country,
    }
    return {
        "result": {"code": 0, "message": "SUCCESS"},
        "statGroups": [{"id": statgroup_id, "members": [member]}],
        "leaderboardStats": [_worldsedge_stat(rating, statgroup_id) for rating in profile.ratings],
    }


def aoe2companion_matches_json(matches: list[Match]) -> Body:
    return {"matches": [_aoe2companion_match(match) for match in matches]}


def worldsedge_matches_json(matches: list[Match]) -> Body:
    players = {player.profile_id: player for match in matches for player in match.players}
    return {
        "result": {"code": 0, "message": "SUCCESS"},
        "matchHistoryStats": [_worldsedge_match(match) for match in matches],
        "profiles": [
            {"profile_id": player.profile_id, "alias": player.name} for player in players.values()
        ],
    }


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


def _worldsedge_stat(rating: Rating, statgroup_id: int) -> Body:
    return {
        "statgroup_id": statgroup_id,
        "leaderboard_id": _worldsedge_leaderboard_id(rating.leaderboard),
        "rating": rating.rating,
        "rank": WORLDSEDGE_NO_RANK if rating.rank is None else rating.rank,
        "wins": rating.wins,
        "losses": rating.losses,
        "streak": rating.streak,
        "highestrating": (
            WORLDSEDGE_NO_HIGHEST_RATING if rating.highest_rating is None else rating.highest_rating
        ),
        "lastmatchdate": _epoch_seconds(rating.last_match),
    }


def _aoe2companion_match(match: Match) -> Body:
    players_by_team = groupby(match.players, key=lambda player: player.team)
    return {
        "matchId": match.match_id,
        "started": _iso_timestamp(match.started),
        "finished": _iso_timestamp(match.finished),
        "leaderboardId": None if match.leaderboard is None else match.leaderboard.value,
        "mapName": match.map_name,
        "teams": [
            {"teamId": team, "players": [_aoe2companion_player(player) for player in players]}
            for team, players in players_by_team
        ],
    }


def _aoe2companion_player(player: MatchPlayer) -> Body:
    return {
        "profileId": player.profile_id,
        "name": player.name,
        "team": player.team,
        "civName": player.civ,
        "rating": _rating_before_match(player),
        "ratingDiff": player.rating_change,
        "won": player.won,
    }


def _worldsedge_match(match: Match) -> Body:
    return {
        "id": match.match_id,
        "mapname": None if match.map_name is None else f"{match.map_name}.rms",
        "matchtype_id": WORLDSEDGE_MATCH_TYPES_BY_LEADERBOARD.get(match.leaderboard),
        "startgametime": _epoch_seconds(match.started),
        "completiontime": _epoch_seconds(match.finished),
        "matchhistorymember": [_worldsedge_member(player) for player in match.players],
    }


def _worldsedge_member(player: MatchPlayer) -> Body:
    return {
        "profile_id": player.profile_id,
        "teamid": None if player.team is None else player.team - 1,
        "oldrating": _rating_before_match(player),
        "newrating": player.rating_after_match,
        "outcome": _worldsedge_outcome(player.won),
        "civilization_id": WORLDSEDGE_UNKNOWN_CIV,
    }


def _rating_before_match(player: MatchPlayer) -> int | None:
    if player.rating_after_match is None or player.rating_change is None:
        return player.rating_after_match
    return player.rating_after_match - player.rating_change


def _worldsedge_outcome(won: bool | None) -> int | None:
    if won is None:
        return None
    return OUTCOME_WIN if won else OUTCOME_LOSS


def _worldsedge_leaderboard_id(leaderboard: Leaderboard) -> int:
    if leaderboard not in WORLDSEDGE_IDS_BY_LEADERBOARD:
        raise ValueError(f"World's Edge has no {leaderboard} leaderboard")
    return WORLDSEDGE_IDS_BY_LEADERBOARD[leaderboard]


def _iso_timestamp(moment: datetime | None) -> str | None:
    return None if moment is None else moment.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _epoch_seconds(moment: datetime | None) -> int:
    return WORLDSEDGE_NO_DATE if moment is None else int(moment.timestamp())
