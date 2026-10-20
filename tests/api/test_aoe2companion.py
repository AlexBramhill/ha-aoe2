from typing import Any

import pytest

from custom_components.aoe2.api import AoeClientResponseError
from custom_components.aoe2.api._aoe2companion import (
    parse_matches,
    parse_profile,
)
from tests.api.helpers import read_fixture

KINGSTONE_PROFILE_ID = 2776293


@pytest.fixture
def matches_response() -> dict[str, Any]:
    return read_fixture("aoe2companion_matches.json")


def test_match_player_includes_civ_name(matches_response: dict[str, Any]):
    # When
    newest_match = parse_matches(matches_response)[0]

    # Then
    assert newest_match.player_with_id(KINGSTONE_PROFILE_ID).civ == "Persians"


def test_malformed_profile_raises_response_error():
    # Given
    malformed_profile = {"name": "missing profileId"}

    # When / Then
    with pytest.raises(AoeClientResponseError):
        parse_profile(malformed_profile)
