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


def test_malformed_profile_raises_response_error():
    # Given
    malformed_profile = {"name": "missing profileId"}

    # When / Then
    with pytest.raises(AoeClientResponseError):
        parse_profile(malformed_profile)
