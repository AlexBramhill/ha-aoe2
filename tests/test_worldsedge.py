import pytest

from custom_components.aoe2.api import (
    AoeClientNotFoundError,
    AoeClientResponseError,
    Leaderboard,
)
from custom_components.aoe2.api._worldsedge import (
    _raise_for_result,
    parse_matches,
    parse_profile,
    parse_search,
    pretty_map_name,
)

VIPER = 196240


def test_parse_profile(load_fixture):
    profile = parse_profile(load_fixture("worldsedge_stat.json"), VIPER)

    assert profile.name == "Oni.TheViper"
    rm = profile.rating_for(Leaderboard.RM_1V1)
    assert (rm.rating, rm.rank, rm.wins, rm.losses) == (2771, 23, 1827, 1010)
    assert profile.rating_for(Leaderboard.RM_TEAM).rating == 1903


def test_parse_profile_unknown_id(load_fixture):
    with pytest.raises(AoeClientNotFoundError):
        parse_profile(load_fixture("worldsedge_stat.json"), 1)


def test_parse_matches_sorted_newest_first(load_fixture):
    matches = parse_matches(load_fixture("worldsedge_matches.json"))

    assert [m.started for m in matches] == sorted((m.started for m in matches), reverse=True)
    newest = matches[0]
    assert newest.match_id == 492055484
    assert newest.leaderboard is Leaderboard.RM_TEAM
    assert newest.map_name == "Coastal Forest"
    viper = newest.player_with_id(VIPER)
    assert (viper.rating, viper.rating_change) == (1868, 18)
    assert viper.civ is None


def test_parse_search(load_fixture):
    results = parse_search(load_fixture("worldsedge_stat.json"))

    assert results[0].profile_id == VIPER


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("CoastalForest.rms", "Coastal Forest"),
        ("budapest.rms2", "budapest"),
        ("BR_FallOfAxum.rms", "BR Fall Of Axum"),
        ("my map", "my map"),
        (None, None),
    ],
)
def test_pretty_map_name(raw, expected):
    assert pretty_map_name(raw) == expected


@pytest.mark.parametrize(
    ("code", "message", "expected"),
    [
        (6, "UNKNOWN_PROFILE_IDS", AoeClientNotFoundError),
        (9, "UNKNOWN_ALIASES", AoeClientNotFoundError),
        (1, "SOMETHING_ELSE", AoeClientResponseError),
    ],
)
def test_raise_for_result(code, message, expected):
    with pytest.raises(expected):
        _raise_for_result({"result": {"code": code, "message": message}})


def test_raise_for_result_ok():
    _raise_for_result({"result": {"code": 0, "message": "SUCCESS"}})


def test_unexpected_shape_raises_response_error():
    with pytest.raises(AoeClientResponseError):
        parse_matches({"matchHistoryStats": [{"id": 1}]})
