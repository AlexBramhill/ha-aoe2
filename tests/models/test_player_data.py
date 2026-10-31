from datetime import timedelta

import pytest

from custom_components.aoe2.models import MatchResult, PlayerData
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
    assert [match.match_id for match in data.matches] == [2, 1]


def test_matches_the_player_did_not_play_in_are_rejected():
    # Given
    someone_elses_match = MatchBuilder().with_match_id(9).build()
    other_player = ProfileBuilder().with_profile_id(999).build().expected

    # When / Then
    with pytest.raises(ValueError, match="did not play in matches \\[9\\]"):
        PlayerData(profile=other_player, unsorted_matches=[someone_elses_match])


def test_recent_win_rate_counts_finished_matches():
    # Given
    data = data_with(WON_MATCH, LOST_MATCH, MatchBuilder().with_match_id(3).unfinished())

    # When
    win_rate = data.recent_win_rate()

    # Then
    assert win_rate == 0.5


def test_recent_win_rate_is_unknown_without_finished_matches():
    # Given
    data = data_with(MatchBuilder().unfinished())

    # When
    win_rate = data.recent_win_rate()

    # Then
    assert win_rate is None


def test_recent_rating_change_sums_finished_matches():
    # Given
    data = data_with(WON_MATCH, LOST_MATCH)

    # When
    change = data.recent_rating_change()

    # Then
    assert change == 10 - 14


def test_last_match_result_is_from_newest_finished_match():
    # Given
    data = data_with(MatchBuilder().with_match_id(3).unfinished(), LOST_MATCH, WON_MATCH)

    # When
    result = data.last_match_result()

    # Then
    assert result is MatchResult.LOSS


def test_last_match_result_is_none_without_finished_matches():
    # Given
    data = data_with(MatchBuilder().unfinished())

    # When
    result = data.last_match_result()

    # Then
    assert result is None


def test_last_match_result_is_unknown_when_the_outcome_is_unknown():
    # Given
    data = data_with(MatchBuilder().with_player(build_match_player(PROFILE_ID, is_winner=None)))

    # When
    result = data.last_match_result()

    # Then
    assert result is MatchResult.UNKNOWN
