import pytest

from custom_components.aoe2.api import AoeClientResponseError
from custom_components.aoe2.api._aoe2companion import (
    parse_matches,
    parse_profile,
)
from tests.api.api_json import Body
from tests.api.helpers import VIPER, VIPER_WON_RANKED_MATCH_ID

KINGSTONE_PROFILE_ID = 2776293


@pytest.fixture
def matches_response() -> Body:
    return VIPER.read_fixture("aoe2companion_matches.json")


def test_match_player_includes_civ_name(matches_response: Body):
    # When
    newest_match = parse_matches(matches_response)[0]

    # Then
    kingstone = newest_match.player_with_id(KINGSTONE_PROFILE_ID)
    assert kingstone is not None
    assert kingstone.civ == "Persians"


def test_match_reports_map_played(matches_response: Body):
    # When
    matches = parse_matches(matches_response)

    # Then
    ranked_match = next(match for match in matches if match.match_id == VIPER_WON_RANKED_MATCH_ID)
    assert ranked_match.map_name == "Arabian Desert"


def ai_match_response() -> Body:
    """Trimmed from match 514342568: a human team against AI players."""
    human = {
        "profileId": 1241154,
        "name": "Steve Onager",
        "team": 1,
        "civName": "Danes",
        "rating": 1238,
        "ratingDiff": 0,
        "won": True,
    }
    ai = {
        "profileId": -1,
        "name": "AI",
        "team": 2,
        "civName": "Malians",
        "rating": None,
        "ratingDiff": None,
        "won": None,
    }
    return {
        "matches": [
            {
                "matchId": 514342568,
                "started": "2026-10-17T16:56:39.000Z",
                "finished": "2026-10-17T17:28:33.000Z",
                "leaderboardId": "unranked",
                "mapName": "Black Forest",
                "teams": [{"teamId": 1, "players": [human]}, {"teamId": 2, "players": [ai]}],
            }
        ]
    }


def test_ai_player_has_name_team_and_civ_but_no_result():
    # When
    match = parse_matches(ai_match_response())[0]

    # Then
    ai = match.player_with_id(-1)
    assert ai is not None
    assert (ai.name, ai.team, ai.civ) == ("AI", 2, "Malians")
    assert (ai.won, ai.rating_after_match, ai.rating_change) == (None, None, None)


def test_rating_after_match_is_unknown_without_rating_change():
    # Given
    response = ai_match_response()
    human = response["matches"][0]["teams"][0]["players"][0]
    human["ratingDiff"] = None

    # When
    match = parse_matches(response)[0]

    # Then
    player = match.player_with_id(1241154)
    assert player is not None
    assert player.rating_after_match is None


def test_malformed_profile_raises_response_error():
    # Given
    malformed_profile = {"name": "missing profileId"}

    # When / Then
    with pytest.raises(AoeClientResponseError):
        parse_profile(malformed_profile)
