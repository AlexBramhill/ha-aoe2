import pytest

from custom_components.aoe2.api import AoeClientResponseError, Leaderboard, _aoe2companion
from custom_components.aoe2.api._aoe2companion import (
    LEADERBOARDS_BY_ID,
    Aoe2CompanionClient,
    parse_matches,
    parse_profile,
)
from tests.api.api_json import Body
from tests.api.helpers import TEST_USER_AGENT, UNUSED_SESSION, VIPER, VIPER_WON_RANKED_MATCH_ID

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


@pytest.fixture
def matches_response() -> Body:
    return VIPER.read_fixture("aoe2companion_matches.json")


def test_match_player_includes_civ_name(matches_response: Body):
    # When
    newest_match = parse_matches(matches_response)[0]

    # Then
    kingstone = newest_match.player_with_id(KINGSTONE_PROFILE_ID)
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
    assert player.rating_after_match is None


def test_match_on_unrecognised_leaderboard_is_other():
    # Given
    response = ai_match_response()
    response["matches"][0]["leaderboardId"] = "brand_new_mode"

    # When
    match = parse_matches(response)[0]

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
    parsed = parse_profile(profile)

    # Then
    assert [rating.leaderboard for rating in parsed.ratings] == [Leaderboard.RM_TEAM]


def test_malformed_profile_raises_response_error():
    # Given
    malformed_profile = {"name": "missing profileId"}

    # When / Then
    with pytest.raises(AoeClientResponseError):
        parse_profile(malformed_profile)


def test_profile_url_links_to_aoe2companion_profile():
    # Given
    client = Aoe2CompanionClient(UNUSED_SESSION, TEST_USER_AGENT)

    # When
    url = client.profile_url(VIPER.profile_id)

    # Then
    assert url == "https://www.aoe2companion.com/profile/196240"


def test_attribution_credits_aoe2companion():
    # Given
    client = Aoe2CompanionClient(UNUSED_SESSION, TEST_USER_AGENT)

    # Then
    assert "aoe2companion" in client.attribution


def test_every_leaderboard_except_other_has_an_aoe2companion_id():
    # Given
    mapped = set(LEADERBOARDS_BY_ID.values())

    # Then
    assert mapped == set(Leaderboard) - {Leaderboard.OTHER}


def test_website_url_is_aoe2companion():
    # Given
    client = Aoe2CompanionClient(UNUSED_SESSION, TEST_USER_AGENT)

    # Then
    assert client.website_url == "https://www.aoe2companion.com"


async def test_requests_send_the_client_user_agent(monkeypatch: pytest.MonkeyPatch):
    # Given
    sent_user_agents: list[str] = []

    async def recording_get_json(*_args: object, user_agent: str) -> Body:
        sent_user_agents.append(user_agent)
        return {"profileId": VIPER.profile_id, "name": "Viper", "leaderboards": []}

    monkeypatch.setattr(_aoe2companion, "get_json", recording_get_json)
    client = Aoe2CompanionClient(UNUSED_SESSION, TEST_USER_AGENT)

    # When
    await client.get_profile(VIPER.profile_id)

    # Then
    assert sent_user_agents == [TEST_USER_AGENT]
