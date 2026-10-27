import pytest

from custom_components.aoe2.api import Leaderboard
from tests.builders import MatchBuilder, build_rating

ABSENT_PROFILE_ID = 999


def test_player_with_id_finds_player_in_match():
    # Given
    match = MatchBuilder().build()

    # When
    player = match.player_with_id(2)

    # Then
    assert player.profile_id == 2


def test_player_with_id_raises_for_player_not_in_match():
    # Given
    match = MatchBuilder().build()

    # When / Then
    with pytest.raises(LookupError):
        match.player_with_id(ABSENT_PROFILE_ID)


def test_win_rate_is_wins_over_games():
    # Given
    rating = build_rating(Leaderboard.RM_1V1, 1500, wins=3, losses=1)

    # Then
    assert rating.win_rate == 0.75


def test_win_rate_is_unknown_without_games():
    # Given
    rating = build_rating(Leaderboard.RM_1V1, 1500, wins=0, losses=0)

    # Then
    assert rating.win_rate is None
