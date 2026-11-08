from custom_components.aoe2.ha._sensor_values import (
    get_current_match_details,
    get_known_result,
    get_last_match_details,
)
from custom_components.aoe2.models import Leaderboard, PlayerData
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


def test_known_result_hides_an_unknown_outcome():
    # Given
    player = build_match_player(PROFILE_ID, is_winner=None)

    # When
    result = get_known_result(player)

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

    match = team_game.build()

    # When
    details = get_last_match_details(match, match.get_player_with_id(PROFILE_ID))

    # Then
    assert details["teammates"] == ["Ally"]
    assert details["opponents"] == ["Player 2", "Rival"]
