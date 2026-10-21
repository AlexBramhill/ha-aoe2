import pytest
from homeassistant.const import STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry

from custom_components.aoe2.api import AoeClientConnectionError, Leaderboard
from custom_components.aoe2.coordinator import Aoe2Data
from custom_components.aoe2.sensor import (
    last_match_details,
    last_match_result,
    recent_rating_change,
    recent_win_rate,
)
from tests.api.builders import MatchBuilder, ProfileBuilder, build_match_player
from tests.fake_client import FakeAoeClient
from tests.integration import (
    PROFILE_ID,
    entity_id_for,
    refresh,
    set_up_integration,
    state_of,
)

PLAYER = ProfileBuilder().with_profile_id(PROFILE_ID).build().expected
WON_MATCH = MatchBuilder().with_match_id(1)
LOST_MATCH = (
    MatchBuilder()
    .with_match_id(2)
    .with_player(build_match_player(PROFILE_ID, rating_change=-14, won=False))
)


def data_with(*matches: MatchBuilder) -> Aoe2Data:
    return Aoe2Data(profile=PLAYER, matches=tuple(match.build() for match in matches))


def test_last_match_result_is_from_newest_finished_match():
    # Given
    data = data_with(MatchBuilder().with_match_id(3).unfinished(), LOST_MATCH, WON_MATCH)

    # When
    result = last_match_result(data)

    # Then
    assert result == "loss"


def test_last_match_result_is_unknown_without_finished_matches():
    # Given
    data = data_with(MatchBuilder().unfinished())

    # When
    result = last_match_result(data)

    # Then
    assert result is None


def test_last_match_details_list_teammates_and_opponents():
    # Given
    team_game = (
        MatchBuilder()
        .with_leaderboard(Leaderboard.RM_TEAM)
        .with_player(build_match_player(3, name="Ally"))
        .with_player(build_match_player(4, name="Rival", team=2))
    )

    # When
    details = last_match_details(data_with(team_game))

    # Then
    assert details["teammates"] == ["Ally"]
    assert details["opponents"] == ["Player 2", "Rival"]


def test_recent_win_rate_counts_finished_matches():
    # Given
    data = data_with(WON_MATCH, LOST_MATCH, MatchBuilder().with_match_id(3).unfinished())

    # When
    win_rate = recent_win_rate(data)

    # Then
    assert win_rate == 50.0


def test_recent_win_rate_is_unknown_without_finished_matches():
    # Given
    data = data_with(MatchBuilder().unfinished())

    # When
    win_rate = recent_win_rate(data)

    # Then
    assert win_rate is None


def test_recent_rating_change_sums_finished_matches():
    # Given
    data = data_with(WON_MATCH, LOST_MATCH)

    # When
    change = recent_rating_change(data)

    # Then
    assert change == 10 - 14


@pytest.mark.usefixtures("created_client_names")
async def test_rating_sensors_show_each_leaderboard(hass: HomeAssistant):
    # When
    await set_up_integration(hass)

    # Then
    assert state_of(hass, Platform.SENSOR, "rm_1v1_rating").state == "1650"
    assert state_of(hass, Platform.SENSOR, "rm_1v1_rank").state == "4200"
    assert state_of(hass, Platform.SENSOR, "rm_team_rating").state == "1580"


@pytest.mark.usefixtures("created_client_names")
async def test_last_match_sensors_describe_newest_match(hass: HomeAssistant):
    # When
    await set_up_integration(hass)

    # Then
    result = state_of(hass, Platform.SENSOR, "last_match_result")
    assert result.state == "win"
    assert result.attributes["map"] == "Arabia"
    assert state_of(hass, Platform.SENSOR, "last_match_rating_change").state == "10"
    assert state_of(hass, Platform.SENSOR, "last_played").state == "2026-10-01T18:35:00+00:00"


@pytest.mark.usefixtures("created_client_names")
async def test_last_updated_records_successful_refresh(hass: HomeAssistant):
    # When
    await set_up_integration(hass)

    # Then
    assert state_of(hass, Platform.SENSOR, "last_updated").state != STATE_UNAVAILABLE


@pytest.mark.usefixtures("created_client_names")
@pytest.mark.parametrize(
    "unique_key",
    ["rm_1v1_wins", "rm_1v1_win_rate", "last_match_map", "recent_win_rate"],
)
async def test_detail_sensors_are_disabled_by_default(hass: HomeAssistant, unique_key: str):
    # When
    await set_up_integration(hass)

    # Then
    entity_id = entity_id_for(hass, Platform.SENSOR, unique_key)
    registry_entry = entity_registry.async_get(hass).async_get(entity_id)
    assert registry_entry is not None
    assert registry_entry.disabled_by is entity_registry.RegistryEntryDisabler.INTEGRATION


@pytest.mark.usefixtures("created_client_names")
async def test_sensors_become_unavailable_when_refresh_fails(
    hass: HomeAssistant, fake_client: FakeAoeClient
):
    # Given
    entry = await set_up_integration(hass)
    fake_client.error = AoeClientConnectionError("unreachable")

    # When
    await refresh(hass, entry)

    # Then
    assert state_of(hass, Platform.SENSOR, "rm_1v1_rating").state == STATE_UNAVAILABLE
