import logging

import pytest
from homeassistant.const import STATE_UNAVAILABLE, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry

from custom_components.aoe2.api import AoeClientConnectionError, Leaderboard
from tests.builders import ProfileBuilder, build_rating
from tests.fake_client import FakeAoeClient
from tests.integration import (
    entity_id_for,
    refresh,
    set_up_integration,
    state_of,
)


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


@pytest.mark.usefixtures("created_client_names")
async def test_rating_sensors_appear_for_newly_played_leaderboard(
    hass: HomeAssistant, fake_client: FakeAoeClient
):
    # Given
    entry = await set_up_integration(hass)
    fake_client.profile = (
        ProfileBuilder().with_rating(build_rating(Leaderboard.EW_1V1, 1400)).build().expected
    )

    # When
    await refresh(hass, entry)

    # Then
    assert state_of(hass, Platform.SENSOR, "ew_1v1_rating").state == "1400"
    assert state_of(hass, Platform.SENSOR, "rm_1v1_rating").state == "1650"


@pytest.mark.usefixtures("created_client_names")
async def test_refresh_does_not_add_existing_rating_sensors_again(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
):
    # Given
    entry = await set_up_integration(hass)

    # When
    await refresh(hass, entry)
    await refresh(hass, entry)

    # Then
    assert not [record for record in caplog.records if record.levelno >= logging.ERROR]
