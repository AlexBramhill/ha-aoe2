from collections.abc import Callable
from datetime import UTC, datetime

import pytest

from custom_components.aoe2.api import (
    AoeClient,
    AoeClientNotFoundError,
    Leaderboard,
    Match,
    create_client,
)
from tests.api.builders import ProfileBuilder, build_rating
from tests.api.fake_apis import FAKE_APIS, FakeApi
from tests.api.helpers import VIPER_PROFILE_ID

UNKNOWN_PROFILE_ID = 1

RECORDED_MATCH_IDS = [515058973, 515058199, 515051663, 515046591, 515041058, 514828647]
LOST_UNRANKED_MATCH_ID = 515058973
WON_RANKED_MATCH_ID = 514828647


RANKED_PLAYER = ProfileBuilder(profile_id=42, name="Ranked", country="gb").with_rating(
    build_rating(
        Leaderboard.RM_1V1,
        1500,
        rank=120,
        wins=30,
        losses=20,
        streak=-2,
        highest_rating=1620,
        last_match=datetime(2026, 1, 2, 3, 4, 5, tzinfo=UTC),
    )
)
UNRANKED_PLAYER = ProfileBuilder(profile_id=43, name="Unranked").with_rating(
    build_rating(Leaderboard.EW_1V1, 1000)
)
NEW_PLAYER = ProfileBuilder(profile_id=44, name="New")


def match_with_id(matches: list[Match], match_id: int) -> Match:
    return next(match for match in matches if match.match_id == match_id)


type Connect = Callable[[FakeApi], AoeClient]


@pytest.fixture(params=FAKE_APIS, ids=lambda fake_api: fake_api.name)
def fake_api(request: pytest.FixtureRequest) -> FakeApi:
    return request.param


@pytest.fixture
def connect(monkeypatch: pytest.MonkeyPatch) -> Connect:
    def connect_to(fake_api: FakeApi) -> AoeClient:
        monkeypatch.setattr(fake_api.module, "get_json", fake_api.get_json)
        return create_client(fake_api.name, session=None)

    return connect_to


@pytest.fixture
def client(fake_api: FakeApi, connect: Connect) -> AoeClient:
    return connect(fake_api)


@pytest.mark.parametrize(
    "builder",
    [RANKED_PLAYER, UNRANKED_PLAYER, NEW_PLAYER],
    ids=["ranked", "unranked", "new"],
)
async def test_built_profile_is_parsed_as_expected(
    fake_api: FakeApi, connect: Connect, builder: ProfileBuilder
):
    # Given
    client = connect(fake_api.serving_profile(builder))

    # When
    profile = await client.get_profile(builder.profile_id)

    # Then
    assert profile == builder.expected_profile()


async def test_unknown_profile_raises_not_found(client: AoeClient):
    # When / Then
    with pytest.raises(AoeClientNotFoundError):
        await client.get_profile(UNKNOWN_PROFILE_ID)


async def test_matches_are_newest_first(client: AoeClient):
    # When
    matches = await client.get_recent_matches(VIPER_PROFILE_ID)

    # Then
    start_times = [match.started for match in matches]
    assert start_times == sorted(start_times, reverse=True)


async def test_matches_include_requested_player(client: AoeClient):
    # When
    matches = await client.get_recent_matches(VIPER_PROFILE_ID)

    # Then
    assert matches
    assert all(match.player_with_id(VIPER_PROFILE_ID) for match in matches)


async def test_match_times_are_timezone_aware(client: AoeClient):
    # When
    matches = await client.get_recent_matches(VIPER_PROFILE_ID)

    # Then
    for match in matches:
        assert match.started.tzinfo is not None
        assert match.finished is None or match.finished.tzinfo is not None


async def test_matches_are_the_recorded_games(client: AoeClient):
    # When
    matches = await client.get_recent_matches(VIPER_PROFILE_ID, count=len(RECORDED_MATCH_IDS))

    # Then
    assert [match.match_id for match in matches] == RECORDED_MATCH_IDS


async def test_lost_match_reports_result_and_rating(client: AoeClient):
    # Given
    matches = await client.get_recent_matches(VIPER_PROFILE_ID, count=len(RECORDED_MATCH_IDS))

    # When
    viper = match_with_id(matches, LOST_UNRANKED_MATCH_ID).player_with_id(VIPER_PROFILE_ID)

    # Then
    assert viper.won is False
    assert viper.rating_change == -20
    assert viper.rating_after_match == 1695


async def test_ranked_match_reports_leaderboard_map_and_rating(client: AoeClient):
    # Given
    matches = await client.get_recent_matches(VIPER_PROFILE_ID, count=len(RECORDED_MATCH_IDS))

    # When
    ranked_match = match_with_id(matches, WON_RANKED_MATCH_ID)

    # Then
    viper = ranked_match.player_with_id(VIPER_PROFILE_ID)
    assert ranked_match.leaderboard is Leaderboard.RM_1V1
    assert ranked_match.map_name == "Arabian Desert"
    assert viper.won is True
    assert viper.rating_change == 4
    assert viper.rating_after_match == 2771


async def test_match_players_have_names(client: AoeClient):
    # When
    matches = await client.get_recent_matches(VIPER_PROFILE_ID)

    # Then
    for match in matches:
        assert all(player.name for player in match.players)


async def test_map_names_are_readable(client: AoeClient):
    # When
    matches = await client.get_recent_matches(VIPER_PROFILE_ID)

    # Then
    for match in matches:
        assert match.map_name
        assert not match.map_name.endswith((".rms", ".rms2"))


async def test_match_count_is_respected(client: AoeClient):
    # When
    matches = await client.get_recent_matches(VIPER_PROFILE_ID, count=1)

    # Then
    assert len(matches) == 1
