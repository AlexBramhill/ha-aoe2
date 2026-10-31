import pytest

from tests.builders import MatchBuilder

ABSENT_PROFILE_ID = 999


def test_has_player_with_id_is_true_for_player_in_match():
    # Given
    match = MatchBuilder().build()

    # When / Then
    assert match.has_player_with_id(2)


def test_has_player_with_id_is_false_for_player_not_in_match():
    # Given
    match = MatchBuilder().build()

    # When / Then
    assert not match.has_player_with_id(ABSENT_PROFILE_ID)


def test_get_player_with_id_finds_player_in_match():
    # Given
    match = MatchBuilder().build()

    # When
    player = match.get_player_with_id(2)

    # Then
    assert player.profile_id == 2


def test_get_player_with_id_raises_for_player_not_in_match():
    # Given
    match = MatchBuilder().build()

    # When / Then
    with pytest.raises(LookupError):
        match.get_player_with_id(ABSENT_PROFILE_ID)
