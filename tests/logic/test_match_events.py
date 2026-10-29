from dataclasses import asdict

from custom_components.aoe2.logic import get_match_finished_event
from custom_components.aoe2.models import Leaderboard
from tests.builders import MatchBuilder, build_match_player


def test_event_is_for_the_requested_player():
    # Given
    match = MatchBuilder().build()

    # When
    event = get_match_finished_event(match, profile_id=2)

    # Then
    assert event.profile_id == 2
    assert event.won is False


def test_event_is_flat_for_automations():
    # Given
    match = (
        MatchBuilder()
        .with_match_id(7)
        .with_player(build_match_player(3, rating_after_match=1496, rating_change=-14, won=False))
        .build()
    )

    # When
    event = get_match_finished_event(match, profile_id=3)

    # Then
    assert asdict(event) == {
        "profile_id": 3,
        "match_id": 7,
        "leaderboard": Leaderboard.RM_1V1,
        "map_name": "Arabia",
        "won": False,
        "rating_after_match": 1496,
        "rating_change": -14,
    }
