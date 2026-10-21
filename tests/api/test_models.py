import pytest

from tests.api.builders import MatchBuilder

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
