from typing import Any

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
    pretty_map_name,
)
from tests.api.helpers import VIPER_PROFILE_ID, read_fixture


def result_body(code: int, message: str) -> dict[str, Any]:
    return {"result": {"code": code, "message": message}}


@pytest.fixture
def stat_response() -> dict[str, Any]:
    return read_fixture("worldsedge_stat.json")


def test_leaderboard_ids_map_to_leaderboards(stat_response: dict[str, Any]):
    # When
    profile = parse_profile(stat_response, VIPER_PROFILE_ID)

    # Then
    assert {rating.leaderboard for rating in profile.ratings} == {
        Leaderboard.RM_1V1,
        Leaderboard.RM_TEAM,
        Leaderboard.EW_1V1,
        Leaderboard.EW_TEAM,
    }


@pytest.mark.parametrize(
    ("filename", "readable_name"),
    [
        ("CoastalForest.rms", "Coastal Forest"),
        ("budapest.rms2", "budapest"),
        ("BR_FallOfAxum.rms", "BR Fall Of Axum"),
        ("my map", "my map"),
        (None, None),
    ],
)
def test_pretty_map_name(filename: str | None, readable_name: str | None):
    # When
    result = pretty_map_name(filename)

    # Then
    assert result == readable_name


def test_success_result_code_does_not_raise():
    # Given
    success = result_body(0, "SUCCESS")

    # When / Then
    _raise_for_result(success)


@pytest.mark.parametrize(
    ("code", "message", "expected_error"),
    [
        (6, "UNKNOWN_PROFILE_IDS", AoeClientNotFoundError),
        (1, "SOMETHING_ELSE", AoeClientResponseError),
    ],
)
def test_error_result_code_raises(code: int, message: str, expected_error: type[Exception]):
    # Given
    error = result_body(code, message)

    # When / Then
    with pytest.raises(expected_error):
        _raise_for_result(error)


def test_malformed_matches_raise_response_error():
    # Given
    malformed_matches = {"matchHistoryStats": [{"id": 1}]}

    # When / Then
    with pytest.raises(AoeClientResponseError):
        parse_matches(malformed_matches)
