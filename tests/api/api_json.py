from datetime import datetime
from itertools import groupby
from typing import Any

from custom_components.aoe2.api import Leaderboard, Match, MatchPlayer, Profile, Rating
from custom_components.aoe2.api._aoe2companion import LEADERBOARDS_BY_ID

type Body = dict[str, Any]

AOE2COMPANION_IDS_BY_LEADERBOARD = {
    leaderboard: leaderboard_id for leaderboard_id, leaderboard in LEADERBOARDS_BY_ID.items()
}


def aoe2companion_profile_json(profile: Profile) -> Body:
    return {
        "profileId": profile.profile_id,
        "name": profile.name,
        "country": profile.country,
        "leaderboards": [_aoe2companion_leaderboard(rating) for rating in profile.ratings],
    }


def aoe2companion_matches_json(matches: list[Match]) -> Body:
    return {"matches": [_aoe2companion_match(match) for match in matches]}


def _aoe2companion_leaderboard(rating: Rating) -> Body:
    return {
        "leaderboardId": _aoe2companion_leaderboard_id(rating.leaderboard),
        "rating": rating.rating,
        "rank": rating.rank,
        "wins": rating.wins,
        "losses": rating.losses,
        "streak": rating.streak,
        "maxRating": rating.highest_rating,
        "lastMatchTime": _iso_timestamp(rating.last_match),
    }


def _aoe2companion_match(match: Match) -> Body:
    players_by_team = groupby(match.players, key=lambda player: player.team)
    return {
        "matchId": match.match_id,
        "started": _iso_timestamp(match.started),
        "finished": _iso_timestamp(match.finished),
        "leaderboardId": _aoe2companion_leaderboard_id(match.leaderboard),
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


def _rating_before_match(player: MatchPlayer) -> int | None:
    if player.rating_after_match is None or player.rating_change is None:
        return None
    return player.rating_after_match - player.rating_change


def _iso_timestamp(moment: datetime | None) -> str | None:
    return None if moment is None else moment.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _aoe2companion_leaderboard_id(leaderboard: Leaderboard) -> str:
    if leaderboard not in AOE2COMPANION_IDS_BY_LEADERBOARD:
        raise ValueError(f"aoe2companion has no ID for {leaderboard}")
    return AOE2COMPANION_IDS_BY_LEADERBOARD[leaderboard]
