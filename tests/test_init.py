from typing import get_args

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aoe2.api import AoeClientConnectionError, ClientName
from custom_components.aoe2.const import CONF_CLIENT, CONF_PROFILE_ID, DOMAIN
from custom_components.aoe2.coordinator import Aoe2Coordinator
from tests.fake_client import FakeAoeClient

PROFILE_ID = 1


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
async def test_unload_unloads_entry(hass: HomeAssistant):
    # Given
    entry = config_entry_for("aoe2companion")
    await set_up(hass, entry)

    # When
    unloaded = await hass.config_entries.async_unload(entry.entry_id)

    # Then
    assert unloaded
    assert entry.state is ConfigEntryState.NOT_LOADED
