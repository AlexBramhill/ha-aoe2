from custom_components.aoe2.logic import get_match_finished_event
from tests.builders import MatchBuilder


def test_event_is_for_the_requested_player():
    # Given
    match = MatchBuilder().build()

    # When
    event = get_match_finished_event(match, profile_id=2)

    # Then
    assert event.profile_id == 2
    assert event.result.won is False
