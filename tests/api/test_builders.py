from datetime import UTC, datetime
from typing import Any

import pytest

from custom_components.aoe2.api import Leaderboard
from custom_components.aoe2.api._aoe2companion import parse_profile as parse_aoe2companion
from custom_components.aoe2.api._worldsedge import parse_profile as parse_worldsedge
from tests.api.builders import ProfileBuilder, build_rating
from tests.api.helpers import VIPER_PROFILE_ID, read_fixture


def is_subset(expected: Any, actual: Any) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and is_subset(value, actual[key]) for key, value in expected.items()
        )
    if isinstance(expected, list):
        return isinstance(actual, list) and all(
            any(is_subset(item, candidate) for candidate in actual) for item in expected
        )
    return expected == actual


@pytest.fixture
def viper_on_aoe2companion() -> ProfileBuilder:
    return (
        ProfileBuilder(profile_id=VIPER_PROFILE_ID)
        .with_name("TheViper")
        .with_country("no")
        .with_rating(
            build_rating(
                Leaderboard.RM_1V1, 2771, rank=22, wins=1827, losses=1010, streak=3,
                highest_rating=2911, last_match=datetime(2026, 10, 19, 14, 35, 23, tzinfo=UTC),
            )
        )
        .with_rating(
            build_rating(
                Leaderboard.RM_TEAM, 1903, rank=208, wins=155, losses=47, streak=4,
                highest_rating=1903, last_match=datetime(2026, 10, 8, 12, 43, 50, tzinfo=UTC),
            )
        )
        .with_rating(
            build_rating(
                Leaderboard.EW_1V1, 1879, wins=1, losses=4, streak=1,
                highest_rating=1925, last_match=datetime(2024, 4, 30, 16, 56, 9, tzinfo=UTC),
            )
        )
        .with_rating(
            build_rating(
                Leaderboard.UNRANKED, 1695, rank=573, wins=4714, losses=2954, streak=-3,
                highest_rating=1822, last_match=datetime(2026, 10, 20, 16, 15, 56, tzinfo=UTC),
            )
        )
    )


@pytest.fixture
def viper_on_worldsedge() -> ProfileBuilder:
    return (
        ProfileBuilder(profile_id=VIPER_PROFILE_ID)
        .with_name("Oni.TheViper")
        .with_country("de")
        .with_worldsedge_statgroup_id(200)
        .with_rating(
            build_rating(
                Leaderboard.RM_1V1, 2771, rank=22, wins=1827, losses=1010, streak=3,
                highest_rating=2911, last_match=datetime(2026, 10, 19, 14, 35, 23, tzinfo=UTC),
            )
        )
        .with_rating(
            build_rating(
                Leaderboard.RM_TEAM, 1903, rank=210, wins=155, losses=47, streak=4,
                highest_rating=1903, last_match=datetime(2026, 10, 8, 12, 43, 50, tzinfo=UTC),
            )
        )
        .with_rating(
            build_rating(
                Leaderboard.EW_1V1, 1843, wins=150, losses=64, streak=1,
                highest_rating=1916, last_match=datetime(2024, 4, 30, 16, 56, 9, tzinfo=UTC),
            )
        )
        .with_rating(
            build_rating(
                Leaderboard.EW_TEAM, 1039, wins=1, losses=0, streak=1,
                last_match=datetime(2022, 6, 23, 23, 0, 12, tzinfo=UTC),
            )
        )
    )


def test_aoe2companion_response_matches_recorded_response(viper_on_aoe2companion: ProfileBuilder):
    # When
    built = viper_on_aoe2companion.aoe2companion_response()

    # Then
    assert is_subset(built, read_fixture("aoe2companion_profile.json"))


def test_recorded_aoe2companion_response_parses_to_expected_profile(
    viper_on_aoe2companion: ProfileBuilder,
):
    # When
    parsed = parse_aoe2companion(read_fixture("aoe2companion_profile.json"))

    # Then
    assert parsed == viper_on_aoe2companion.expected_profile()


def test_worldsedge_response_matches_recorded_response(viper_on_worldsedge: ProfileBuilder):
    # When
    built = viper_on_worldsedge.worldsedge_response()

    # Then
    assert is_subset(built, read_fixture("worldsedge_stat.json"))


def test_recorded_worldsedge_response_parses_to_expected_profile(
    viper_on_worldsedge: ProfileBuilder,
):
    # When
    parsed = parse_worldsedge(read_fixture("worldsedge_stat.json"), VIPER_PROFILE_ID)

    # Then
    assert parsed == viper_on_worldsedge.expected_profile()


def test_worldsedge_response_rejects_leaderboard_it_does_not_have():
    # Given
    builder = ProfileBuilder().with_rating(build_rating(Leaderboard.UNRANKED, 1500))

    # When / Then
    with pytest.raises(ValueError):
        builder.worldsedge_response()
