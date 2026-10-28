from typing import Any, get_args

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry

from custom_components.aoe2.api import (
    BACKGROUND_REQUESTS,
    AoeClientConnectionError,
    ClientName,
    RequestPolicy,
)
from custom_components.aoe2.const import DOMAIN
from custom_components.aoe2.ha_internals.coordinator import Aoe2Coordinator
from tests.fake_client import FakeAoeClient
from tests.integration import PROFILE_ID, config_entry_for, set_up

PREVIOUS_PROFILE_ID = 2


@pytest.mark.parametrize("client_name", get_args(ClientName))
async def test_setup_uses_configured_client(
    hass: HomeAssistant, created_client_names: list[ClientName], client_name: ClientName
):
    # Given
    entry = config_entry_for(client_name)

    # When
    await set_up(hass, entry)

    # Then
    assert entry.state is ConfigEntryState.LOADED
    assert created_client_names == [client_name]
    assert isinstance(entry.runtime_data, Aoe2Coordinator)


@pytest.mark.usefixtures("created_client_names")
async def test_setup_polls_with_retries(
    hass: HomeAssistant, created_client_policies: list[RequestPolicy]
):
    # Given
    entry = config_entry_for("aoe2companion")

    # When
    await set_up(hass, entry)

    # Then
    assert created_client_policies == [BACKGROUND_REQUESTS]


@pytest.mark.usefixtures("created_client_names")
async def test_setup_retries_when_client_is_unreachable(
    hass: HomeAssistant, fake_client: FakeAoeClient
):
    # Given
    fake_client.error = AoeClientConnectionError("unreachable")
    entry = config_entry_for("aoe2companion")

    # When
    await set_up(hass, entry)

    # Then
    assert entry.state is ConfigEntryState.SETUP_RETRY


@pytest.mark.usefixtures("created_client_names")
async def test_setup_removes_previous_players_device(hass: HomeAssistant):
    # Given
    entry = config_entry_for("aoe2companion")
    entry.add_to_hass(hass)
    devices = device_registry.async_get(hass)
    devices.async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, str(PREVIOUS_PROFILE_ID))}
    )

    # When
    await set_up(hass, entry)

    # Then
    remaining = device_registry.async_entries_for_config_entry(devices, entry.entry_id)
    assert [device.identifiers for device in remaining] == [{(DOMAIN, str(PROFILE_ID))}]


@pytest.mark.usefixtures("created_client_names")
async def test_unload_unloads_entry(hass: HomeAssistant):
    # Given
    entry = config_entry_for("aoe2companion")
    await set_up(hass, entry)

    # When
    unloaded = await hass.config_entries.async_unload(entry.entry_id)

    # Then
    assert unloaded
    assert entry.state is ConfigEntryState.NOT_LOADED


@pytest.mark.usefixtures("created_client_names")
async def test_remove_deletes_saved_announcements(
    hass: HomeAssistant, hass_storage: dict[str, Any]
):
    # Given
    entry = config_entry_for("aoe2companion")
    await set_up(hass, entry)
    storage_key = f"{DOMAIN}.{entry.entry_id}.recorded_matches"
    assert storage_key in hass_storage

    # When
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    # Then
    assert storage_key not in hass_storage
