from collections.abc import Callable
from typing import get_args

import pytest

from custom_components.aoe2.api import (
    AoeClient,
    AoeClientNotFoundError,
    ClientName,
    Leaderboard,
    Match,
    create_client,
)
from tests.api.fake_apis import FAKE_API_FOR_CLIENT, FakeApi
from tests.api.helpers import (
    RECORDED_PLAYERS,
    TEST_VERSION,
    UNUSED_SESSION,
    VIPER,
    VIPER_LOST_UNRANKED_MATCH_ID,
    VIPER_MATCH_IDS,
    VIPER_WON_RANKED_MATCH_ID,
    RecordedPlayer,
)
from tests.builders import (
    BuiltMatchHistory,
    BuiltProfile,
    MatchBuilder,
    ProfileBuilder,
    build_match_history,
    build_match_player,
    build_rating,
)

UNKNOWN_PROFILE_ID = 999_999_999


RANKED_PLAYER = ProfileBuilder().with_profile_id(42).with_name("Ranked").build()
UNRANKED_PLAYER = (
    ProfileBuilder()
    .with_profile_id(43)
    .with_name("Unranked")
    .without_ratings()
    .with_rating(build_rating(Leaderboard.EW_1V1, 1000))
    .build()
)
NEW_PLAYER = ProfileBuilder().with_profile_id(44).with_name("New").without_ratings().build()

ONE_V_ONE_HISTORY = build_match_history(MatchBuilder())
UNFINISHED_HISTORY = build_match_history(MatchBuilder().unfinished())
TEAM_GAME_HISTORY = build_match_history(
    MatchBuilder()
    .with_leaderboard(Leaderboard.RM_TEAM)
    .with_player(build_match_player(3))
    .with_player(build_match_player(4, team=2, rating_change=-12, won=False))
)

type Connect = Callable[[FakeApi], AoeClient]


def match_with_id(matches: list[Match], match_id: int) -> Match:
    return next(match for match in matches if match.match_id == match_id)


@pytest.fixture(params=get_args(ClientName))
def client_name(request: pytest.FixtureRequest) -> ClientName:
    return request.param


@pytest.fixture(params=RECORDED_PLAYERS, ids=lambda player: player.name)
def recorded_player(request: pytest.FixtureRequest) -> RecordedPlayer:
    return request.param


@pytest.fixture
def connect(monkeypatch: pytest.MonkeyPatch) -> Connect:
    def connect_to(fake_api: FakeApi) -> AoeClient:
        monkeypatch.setattr(fake_api.module, "get_json", fake_api.get_json)
        return create_client(fake_api.name, session=UNUSED_SESSION, version=TEST_VERSION)

    return connect_to


@pytest.fixture
def client(client_name: ClientName, recorded_player: RecordedPlayer, connect: Connect) -> AoeClient:
    return connect(FAKE_API_FOR_CLIENT[client_name](recorded_player))


@pytest.fixture
def viper_fake_api(client_name: ClientName) -> FakeApi:
    return FAKE_API_FOR_CLIENT[client_name](VIPER)


@pytest.fixture
def viper_client(viper_fake_api: FakeApi, connect: Connect) -> AoeClient:
    return connect(viper_fake_api)


@pytest.mark.parametrize(
    "player",
    [RANKED_PLAYER, UNRANKED_PLAYER, NEW_PLAYER],
    ids=["ranked", "unranked", "new"],
)
async def test_built_profile_is_parsed_as_expected(
    viper_fake_api: FakeApi, connect: Connect, player: BuiltProfile
):
    # Given
    client = connect(viper_fake_api.serving_profile(player))

    # When
    profile = await client.get_profile(player.expected.profile_id)

    # Then
    assert profile == player.expected


@pytest.mark.parametrize(
    "history",
    [ONE_V_ONE_HISTORY, UNFINISHED_HISTORY, TEAM_GAME_HISTORY],
    ids=["1v1", "unfinished", "team-game"],
)
async def test_built_matches_are_parsed_as_expected(
    viper_fake_api: FakeApi, connect: Connect, history: BuiltMatchHistory
):
    # Given
    client = connect(viper_fake_api.serving_matches(history))

    # When
    matches = await client.get_recent_matches(profile_id=1)

    # Then
    assert matches == history.expected


async def test_unknown_profile_raises_not_found(client: AoeClient):
    # When / Then
    with pytest.raises(AoeClientNotFoundError):
        await client.get_profile(UNKNOWN_PROFILE_ID)


async def test_matches_are_newest_first(client: AoeClient, recorded_player: RecordedPlayer):
    # When
    matches = await client.get_recent_matches(recorded_player.profile_id)

    # Then
    start_times = [match.started for match in matches]
    assert start_times == sorted(start_times, reverse=True)


async def test_matches_include_requested_player(client: AoeClient, recorded_player: RecordedPlayer):
    # When
    matches = await client.get_recent_matches(recorded_player.profile_id)

    # Then
    assert matches
    for match in matches:
        match.get_player_with_id(recorded_player.profile_id)


async def test_match_times_are_timezone_aware(client: AoeClient, recorded_player: RecordedPlayer):
    # When
    matches = await client.get_recent_matches(recorded_player.profile_id)

    # Then
    for match in matches:
        assert match.started.tzinfo is not None
        assert match.finished is None or match.finished.tzinfo is not None


async def test_match_players_have_names(client: AoeClient, recorded_player: RecordedPlayer):
    # When
    matches = await client.get_recent_matches(recorded_player.profile_id)

    # Then
    for match in matches:
        assert all(player.name for player in match.players)


async def test_teams_are_numbered_from_one(client: AoeClient, recorded_player: RecordedPlayer):
    # When
    matches = await client.get_recent_matches(recorded_player.profile_id)

    # Then
    for match in matches:
        teams = {player.team for player in match.players}
        assert teams == set(range(1, len(teams) + 1))


async def test_matches_have_map_names(client: AoeClient, recorded_player: RecordedPlayer):
    # When
    matches = await client.get_recent_matches(recorded_player.profile_id)

    # Then
    for match in matches:
        assert match.map_name


async def test_match_count_is_respected(client: AoeClient, recorded_player: RecordedPlayer):
    # When
    matches = await client.get_recent_matches(recorded_player.profile_id, count=1)

    # Then
    assert len(matches) == 1


async def test_viper_matches_are_the_recorded_games(viper_client: AoeClient):
    # When
    matches = await viper_client.get_recent_matches(VIPER.profile_id, count=len(VIPER_MATCH_IDS))

    # Then
    assert [match.match_id for match in matches] == VIPER_MATCH_IDS


async def test_viper_lost_match_reports_result_rating_and_team(viper_client: AoeClient):
    # When
    matches = await viper_client.get_recent_matches(VIPER.profile_id, count=len(VIPER_MATCH_IDS))

    # Then
    viper = match_with_id(matches, VIPER_LOST_UNRANKED_MATCH_ID).get_player_with_id(
        VIPER.profile_id
    )
    assert viper.won is False
    assert viper.rating_change == -20
    assert viper.rating_after_match == 1695
    assert viper.team == 2


async def test_viper_ranked_match_reports_leaderboard_rating_and_team(viper_client: AoeClient):
    # When
    matches = await viper_client.get_recent_matches(VIPER.profile_id, count=len(VIPER_MATCH_IDS))

    # Then
    ranked_match = match_with_id(matches, VIPER_WON_RANKED_MATCH_ID)
    viper = ranked_match.get_player_with_id(VIPER.profile_id)
    assert ranked_match.leaderboard is Leaderboard.RM_1V1
    assert viper.won is True
    assert viper.rating_change == 4
    assert viper.rating_after_match == 2771
    assert viper.team == 1
