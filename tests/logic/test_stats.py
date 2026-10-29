from custom_components.aoe2.api import Leaderboard
from custom_components.aoe2.logic import (
    PlayerData,
    get_current_match_details,
    get_last_match_details,
    get_last_match_result,
    get_recent_rating_change,
    get_recent_win_rate,
)
from tests.builders import TYPICAL_START, MatchBuilder, ProfileBuilder, build_match_player
from tests.integration import PROFILE_ID

PLAYER = ProfileBuilder().with_profile_id(PROFILE_ID).build().expected
WON_MATCH = MatchBuilder().with_match_id(1)
LOST_MATCH = (
    MatchBuilder()
    .with_match_id(2)
    .with_player(build_match_player(PROFILE_ID, rating_change=-14, won=False))
)


def data_with(*matches: MatchBuilder) -> PlayerData:
    return PlayerData(profile=PLAYER, matches=tuple(match.build() for match in matches))


def test_last_match_result_is_from_newest_finished_match():
    # Given
    data = data_with(MatchBuilder().with_match_id(3).unfinished(), LOST_MATCH, WON_MATCH)

    # When
    result = get_last_match_result(data)

    # Then
    assert result == "loss"


def test_last_match_result_is_unknown_without_finished_matches():
    # Given
    data = data_with(MatchBuilder().unfinished())

    # When
    result = get_last_match_result(data)

    # Then
    assert result is None


def test_last_match_result_is_unknown_when_the_outcome_is_unknown():
    # Given
    data = data_with(MatchBuilder().with_player(build_match_player(PROFILE_ID, won=None)))

    # When
    result = get_last_match_result(data)

    # Then
    assert result is None


def test_current_match_details_describe_the_unfinished_match():
    # Given
    data = data_with(MatchBuilder().with_match_id(2).with_map_name("Arena").unfinished(), WON_MATCH)

    # When
    details = get_current_match_details(data)

    # Then
    assert details == {
        "leaderboard": Leaderboard.RM_1V1,
        "map": "Arena",
        "started": TYPICAL_START,
    }


def test_current_match_details_are_empty_between_matches():
    # Given
    data = data_with(WON_MATCH)

    # When
    details = get_current_match_details(data)

    # Then
    assert details == {}


def test_last_match_details_list_teammates_and_opponents():
    # Given
    team_game = (
        MatchBuilder()
        .with_leaderboard(Leaderboard.RM_TEAM)
        .with_player(build_match_player(3, name="Ally"))
        .with_player(build_match_player(4, name="Rival", team=2))
    )

    # When
    details = get_last_match_details(data_with(team_game))

    # Then
    assert details["teammates"] == ["Ally"]
    assert details["opponents"] == ["Player 2", "Rival"]


def test_recent_win_rate_counts_finished_matches():
    # Given
    data = data_with(WON_MATCH, LOST_MATCH, MatchBuilder().with_match_id(3).unfinished())

    # When
    win_rate = get_recent_win_rate(data)

    # Then
    assert win_rate == 50.0


def test_recent_win_rate_is_unknown_without_finished_matches():
    # Given
    data = data_with(MatchBuilder().unfinished())

    # When
    win_rate = get_recent_win_rate(data)

    # Then
    assert win_rate is None


def test_recent_rating_change_sums_finished_matches():
    # Given
    data = data_with(WON_MATCH, LOST_MATCH)

    # When
    change = get_recent_rating_change(data)

    # Then
    assert change == 10 - 14
