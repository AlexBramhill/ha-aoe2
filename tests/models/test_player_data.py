from datetime import timedelta

import pytest

from custom_components.aoe2.models import PlayerData
from tests.builders import TYPICAL_START, MatchBuilder, ProfileBuilder, build_match_player
from tests.integration import PROFILE_ID

PLAYER = ProfileBuilder().with_profile_id(PROFILE_ID).build().expected
WON_MATCH = MatchBuilder().with_match_id(1)
LOST_MATCH = (
    MatchBuilder()
    .with_match_id(2)
    .with_player(build_match_player(PROFILE_ID, rating_change=-14, is_winner=False))
)


def data_with(*matches: MatchBuilder) -> PlayerData:
    return PlayerData(profile=PLAYER, unsorted_matches=[match.build() for match in matches])


def test_matches_are_sorted_newest_first():
    # Given
    older = MatchBuilder().with_match_id(1).with_start(TYPICAL_START)
    newer = MatchBuilder().with_match_id(2).with_start(TYPICAL_START + timedelta(hours=1))

    # When
    data = data_with(older, newer)

    # Then
    assert [match.match_id for match in data.matches_newest_first] == [2, 1]


def test_matches_the_player_did_not_play_in_are_rejected():
    # Given
    someone_elses_match = MatchBuilder().with_match_id(9).build()
    other_player = ProfileBuilder().with_profile_id(999).build().expected

    # When / Then
    with pytest.raises(ValueError, match="did not play in matches \\[9\\]"):
        _ = PlayerData(profile=other_player, unsorted_matches=[someone_elses_match])


def test_recent_win_rate_counts_finished_matches():
    # Given
    data = data_with(WON_MATCH, LOST_MATCH, MatchBuilder().with_match_id(3).unfinished())

    # When
    win_rate = data.get_recent_win_rate()

    # Then
    assert win_rate == 0.5


def test_recent_win_rate_ignores_matches_with_an_unknown_outcome():
    # Given
    unknown_outcome = build_match_player(PROFILE_ID, is_winner=None)
    data = data_with(WON_MATCH, MatchBuilder().with_match_id(3).with_player(unknown_outcome))

    # When
    win_rate = data.get_recent_win_rate()

    # Then
    assert win_rate == 1.0


def test_recent_win_rate_is_unknown_without_finished_matches():
    # Given
    data = data_with(MatchBuilder().unfinished())

    # When
    win_rate = data.get_recent_win_rate()

    # Then
    assert win_rate is None


def test_recent_rating_change_sums_finished_matches():
    # Given
    data = data_with(WON_MATCH, LOST_MATCH)

    # When
    change = data.get_recent_rating_change()

    # Then
    assert change == 10 - 14


def test_last_finished_match_is_the_newest_finished_match():
    # Given
    data = data_with(MatchBuilder().with_match_id(3).unfinished(), LOST_MATCH, WON_MATCH)

    # When
    match = data.get_last_finished_match()

    # Then
    assert match is not None
    assert match.match_id == LOST_MATCH.build().match_id


def test_last_finished_match_is_none_without_finished_matches():
    # Given
    data = data_with(MatchBuilder().unfinished())

    # When
    match = data.get_last_finished_match()

    # Then
    assert match is None
