from datetime import UTC, datetime

import pytest

from custom_components.aoe2.api import AoeClientResponseError, Leaderboard
from custom_components.aoe2.api._aoe2companion import (
    parse_matches,
    parse_profile,
    parse_search,
)

VIPER = 196240


def test_parse_profile(load_fixture):
    profile = parse_profile(load_fixture("aoe2companion_profile.json"))

    assert profile.profile_id == VIPER
    assert profile.name == "TheViper"
    rm_1v1 = profile.rating_for(Leaderboard.RM_1V1)
    assert rm_1v1 is not None
    assert (rm_1v1.rating, rm_1v1.rank, rm_1v1.wins, rm_1v1.losses) == (2771, 23, 1827, 1010)
    assert rm_1v1.highest_rating == 2911
    assert rm_1v1.last_match == datetime(2026, 10, 19, 14, 35, 23, tzinfo=UTC)
    assert profile.rating_for(Leaderboard.RM_TEAM).rating == 1903


def test_parse_matches(load_fixture):
    match = parse_matches(load_fixture("aoe2companion_matches.json"))[0]

    assert match.match_id == 515058973
    assert match.leaderboard is Leaderboard.UNRANKED
    assert match.map_name == "Rage Forest 2026 (Custom)"
    assert match.finished > match.started
    kingstone = match.player_with_id(2776293)
    assert (kingstone.civ, kingstone.rating_change, kingstone.won) == ("Persians", 17, True)


def test_parse_search(load_fixture):
    first = parse_search(load_fixture("aoe2companion_search.json"))[0]

    assert (first.profile_id, first.name, first.games) == (VIPER, "TheViper", 11048)


def test_unexpected_shape_raises_response_error():
    with pytest.raises(AoeClientResponseError):
        parse_profile({"name": "missing profileId"})
