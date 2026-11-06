import json

import pytest
from pydantic import ValidationError

from custom_components.aoe2.api import (
    BACKGROUND_REQUESTS,
    INTERACTIVE_REQUESTS,
    RequestPolicy,
    _aoe2companion,
)
from custom_components.aoe2.api._aoe2companion import (
    LEADERBOARDS_BY_ID,
    Aoe2CompanionClient,
    get_matches_from,
    get_profile_from,
)
from custom_components.aoe2.api._aoe2companion_responses import MatchesResponse, ProfileResponse
from custom_components.aoe2.models import Leaderboard, Match, Profile
from tests.api.api_json import Body
from tests.api.helpers import TEST_VERSION, UNUSED_SESSION, VIPER, VIPER_WON_RANKED_MATCH_ID
from tests.json_values import get_object_at

KINGSTONE_PROFILE_ID = 2776293
RATING_JSON = {
    "rating": 1050,
    "rank": 34570,
    "wins": 56,
    "losses": 51,
    "streak": 1,
    "maxRating": 1100,
    "lastMatchTime": "2026-10-18T19:26:00.000Z",
}

VIPER_PROFILE = ProfileResponse(profile_id=VIPER.profile_id, name="Viper")


def parse_profile(body: str) -> Profile:
    return get_profile_from(ProfileResponse.model_validate_json(body))


def parse_matches(body: str) -> list[Match]:
    return get_matches_from(MatchesResponse.model_validate_json(body))


@pytest.fixture
def matches_response() -> str:
    return VIPER.read_fixture_text("aoe2companion_matches.json")


def test_match_player_includes_civ_name(matches_response: str):
    # When
    newest_match = parse_matches(matches_response)[0]

    # Then
    kingstone = newest_match.get_player_with_id(KINGSTONE_PROFILE_ID)
    assert kingstone.civ == "Persians"


def test_match_reports_map_played(matches_response: str):
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
    match = parse_matches(json.dumps(ai_match_response()))[0]

    # Then
    ai = match.get_player_with_id(-1)
    assert (ai.name, ai.team, ai.civ) == ("AI", 2, "Malians")
    assert (ai.is_winner, ai.rating_after_match, ai.rating_change) == (None, None, None)


def test_rating_after_match_is_unknown_without_rating_change():
    # Given
    response = ai_match_response()
    human = get_object_at(response, "matches", 0, "teams", 0, "players", 0)
    human["ratingDiff"] = None

    # When
    match = parse_matches(json.dumps(response))[0]

    # Then
    player = match.get_player_with_id(1241154)
    assert player.rating_after_match is None


def test_match_on_unrecognised_leaderboard_is_other():
    # Given
    response = ai_match_response()
    get_object_at(response, "matches", 0)["leaderboardId"] = "brand_new_mode"

    # When
    match = parse_matches(json.dumps(response))[0]

    # Then
    assert match.leaderboard is Leaderboard.OTHER


def test_profile_skips_ratings_on_unrecognised_leaderboards():
    # Given
    profile = {
        "profileId": 1241154,
        "name": "Steve Onager",
        "leaderboards": [
            {**RATING_JSON, "leaderboardId": "rm_team"},
            {**RATING_JSON, "leaderboardId": "brand_new_mode"},
        ],
    }

    # When
    parsed = parse_profile(json.dumps(profile))

    # Then
    assert [rating.leaderboard for rating in parsed.ratings] == [Leaderboard.RM_TEAM]


def test_profile_without_profile_id_is_rejected():
    # Given
    malformed_profile = {"name": "missing profileId"}

    # When / Then
    with pytest.raises(ValidationError):
        _ = parse_profile(json.dumps(malformed_profile))


def test_mistyped_rating_is_rejected():
    # Given
    profile = {
        "profileId": 1,
        "name": "Player",
        "leaderboards": [{**RATING_JSON, "rating": "1650"}],
    }

    # When / Then
    with pytest.raises(ValidationError):
        _ = parse_profile(json.dumps(profile))


def test_list_response_is_rejected():
    # When / Then
    with pytest.raises(ValidationError):
        _ = parse_matches("[]")


def test_profile_url_links_to_aoe2companion_profile():
    # Given
    client = Aoe2CompanionClient(UNUSED_SESSION, TEST_VERSION)

    # When
    url = client.profile_url(VIPER.profile_id)

    # Then
    assert url == "https://www.aoe2companion.com/profile/196240"


def test_attribution_credits_aoe2companion():
    # Given
    client = Aoe2CompanionClient(UNUSED_SESSION, TEST_VERSION)

    # Then
    assert "aoe2companion" in client.attribution


def test_every_leaderboard_except_other_has_an_aoe2companion_id():
    # Given
    mapped = set(LEADERBOARDS_BY_ID.values())

    # Then
    assert mapped == set(Leaderboard) - {Leaderboard.OTHER}


def test_website_url_is_aoe2companion():
    # Given
    client = Aoe2CompanionClient(UNUSED_SESSION, TEST_VERSION)

    # Then
    assert client.website_url == "https://www.aoe2companion.com"


async def test_requests_send_the_client_version(monkeypatch: pytest.MonkeyPatch):
    # Given
    sent_versions: list[str] = []

    async def recording_get_response(
        *_args: object, version: str, **_options: object
    ) -> ProfileResponse:
        sent_versions.append(version)
        return VIPER_PROFILE

    monkeypatch.setattr(_aoe2companion, "get_response", recording_get_response)
    client = Aoe2CompanionClient(UNUSED_SESSION, TEST_VERSION)

    # When
    _ = await client.get_profile(VIPER.profile_id)

    # Then
    assert sent_versions == [TEST_VERSION]


@pytest.mark.parametrize(
    ("given_policy", "expected_policy"),
    [(None, BACKGROUND_REQUESTS), (INTERACTIVE_REQUESTS, INTERACTIVE_REQUESTS)],
    ids=["default", "interactive"],
)
async def test_requests_use_the_client_policy(
    monkeypatch: pytest.MonkeyPatch,
    given_policy: RequestPolicy | None,
    expected_policy: RequestPolicy,
):
    # Given
    sent_policies: list[RequestPolicy] = []

    async def recording_get_response(
        *_args: object, policy: RequestPolicy, **_options: object
    ) -> ProfileResponse:
        sent_policies.append(policy)
        return VIPER_PROFILE

    monkeypatch.setattr(_aoe2companion, "get_response", recording_get_response)
    client = (
        Aoe2CompanionClient(UNUSED_SESSION, TEST_VERSION)
        if given_policy is None
        else Aoe2CompanionClient(UNUSED_SESSION, TEST_VERSION, given_policy)
    )

    # When
    _ = await client.get_profile(VIPER.profile_id)

    # Then
    assert sent_policies == [expected_policy]
