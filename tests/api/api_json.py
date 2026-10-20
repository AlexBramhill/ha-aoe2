from datetime import datetime
from typing import Any

from custom_components.aoe2.api import Leaderboard, Profile, Rating
from custom_components.aoe2.api._worldsedge import LEADERBOARD_IDS

type Body = dict[str, Any]

WORLDSEDGE_IDS_BY_LEADERBOARD = {
    leaderboard: leaderboard_id for leaderboard_id, leaderboard in LEADERBOARD_IDS.items()
}
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


def _worldsedge_leaderboard_id(leaderboard: Leaderboard) -> int:
    if leaderboard not in WORLDSEDGE_IDS_BY_LEADERBOARD:
        raise ValueError(f"World's Edge has no {leaderboard} leaderboard")
    return WORLDSEDGE_IDS_BY_LEADERBOARD[leaderboard]


def _iso_timestamp(moment: datetime | None) -> str | None:
    return None if moment is None else moment.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _epoch_seconds(moment: datetime | None) -> int:
    return WORLDSEDGE_NO_DATE if moment is None else int(moment.timestamp())
