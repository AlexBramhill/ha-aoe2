from typing import get_args

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aoe2.api import CLIENTS, ClientName
from custom_components.aoe2.const import CONF_CLIENT, CONF_PROFILE_ID, DOMAIN

PROFILE_ID = 196240


def config_entry_for(client_name: ClientName) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        data={CONF_CLIENT: client_name, CONF_PROFILE_ID: PROFILE_ID},
    )


async def set_up(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize("client_name", get_args(ClientName))
async def test_setup_creates_configured_client(hass: HomeAssistant, client_name: ClientName):
    # Given
    entry = config_entry_for(client_name)

    # When
    await set_up(hass, entry)

    # Then
    assert entry.state is ConfigEntryState.LOADED
    assert isinstance(entry.runtime_data, CLIENTS[client_name])


async def test_unload_unloads_entry(hass: HomeAssistant):
    # Given
    entry = config_entry_for("aoe2companion")
    await set_up(hass, entry)

    # When
    unloaded = await hass.config_entries.async_unload(entry.entry_id)

    # Then
    assert unloaded
    assert entry.state is ConfigEntryState.NOT_LOADED
