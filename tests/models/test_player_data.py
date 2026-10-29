from custom_components.aoe2.models import PlayerData
from tests.builders import MatchBuilder, ProfileBuilder, build_match_player
from tests.integration import PROFILE_ID

PLAYER = ProfileBuilder().with_profile_id(PROFILE_ID).build().expected
WON_MATCH = MatchBuilder().with_match_id(1)
LOST_MATCH = (
    MatchBuilder()
    .with_match_id(2)
    .with_player(build_match_player(PROFILE_ID, rating_change=-14, is_winner=False))
)


def data_with(*matches: MatchBuilder) -> PlayerData:
    return PlayerData(profile=PLAYER, matches=tuple(match.build() for match in matches))


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
