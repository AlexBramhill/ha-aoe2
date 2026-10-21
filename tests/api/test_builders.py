from typing import Any

import pytest

from custom_components.aoe2.api import Leaderboard
from tests.api.builders import MatchBuilder, ProfileBuilder, build_match_history, build_rating
from tests.api.helpers import RECORDED_PLAYERS, RecordedPlayer


def has_same_shape(built: Any, recorded: Any) -> bool:
    if built is None or recorded is None:
        return True
    if isinstance(built, dict):
        return isinstance(recorded, dict) and object_has_same_shape(built, recorded)
    if isinstance(built, list):
        return isinstance(recorded, list) and list_has_same_shape(built, recorded)
    return type(built) is type(recorded)


def object_has_same_shape(built: dict[str, Any], recorded: dict[str, Any]) -> bool:
    return all(
        key in recorded and has_same_shape(value, recorded[key]) for key, value in built.items()
    )


def list_has_same_shape(built: list[Any], recorded: list[Any]) -> bool:
    return all(any(has_same_shape(item, candidate) for candidate in recorded) for item in built)


@pytest.mark.parametrize("player", RECORDED_PLAYERS, ids=lambda player: player.name)
def test_aoe2companion_response_has_recorded_shape(player: RecordedPlayer):
    # Given
    recorded = player.read_fixture("aoe2companion_profile.json")

    # When
    built = ProfileBuilder().build()

    # Then
    assert has_same_shape(built.aoe2companion_response, recorded)


@pytest.mark.parametrize("player", RECORDED_PLAYERS, ids=lambda player: player.name)
def test_aoe2companion_matches_have_recorded_shape(player: RecordedPlayer):
    # Given
    recorded = player.read_fixture("aoe2companion_matches.json")

    # When
    built = build_match_history(MatchBuilder())

    # Then
    assert has_same_shape(built.aoe2companion_response, recorded)


def test_default_player_is_complete():
    # When
    built = ProfileBuilder().build()

    # Then
    assert built.expected.country is not None
    assert built.expected.ratings
    for rating in built.expected.ratings:
        assert rating.rank is not None


def test_with_rating_replaces_rating_on_same_leaderboard_in_place():
    # Given
    builder = ProfileBuilder()

    # When
    built = builder.with_rating(build_rating(Leaderboard.RM_1V1, 2000)).build()

    # Then
    ratings = [(rating.leaderboard, rating.rating) for rating in built.expected.ratings]
    assert ratings == [(Leaderboard.RM_1V1, 2000), (Leaderboard.RM_TEAM, 1580)]


def test_without_ratings_builds_player_with_no_games():
    # When
    built = ProfileBuilder().without_ratings().build()

    # Then
    assert built.expected.ratings == ()
