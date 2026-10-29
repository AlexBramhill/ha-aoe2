from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.device_registry import DeviceEntry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aoe2.const import DOMAIN
from custom_components.aoe2.ha_internals.devices import remove_previous_players_devices
from tests.integration import PROFILE_ID, config_entry_for

PREVIOUS_PROFILE_ID = 2


def add_player_device(hass: HomeAssistant, entry: MockConfigEntry, profile_id: int) -> str:
    device = device_registry.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id, identifiers={(DOMAIN, str(profile_id))}
    )
    return device.id


def get_entry_devices(hass: HomeAssistant, entry: MockConfigEntry) -> list[DeviceEntry]:
    devices = device_registry.async_get(hass)
    return device_registry.async_entries_for_config_entry(devices, entry.entry_id)


async def test_previous_players_device_is_removed(hass: HomeAssistant):
    # Given
    entry = config_entry_for()
    entry.add_to_hass(hass)
    add_player_device(hass, entry, PROFILE_ID)
    add_player_device(hass, entry, PREVIOUS_PROFILE_ID)

    # When
    remove_previous_players_devices(hass, entry)

    # Then
    remaining = get_entry_devices(hass, entry)
    assert [device.identifiers for device in remaining] == [{(DOMAIN, str(PROFILE_ID))}]


async def test_previous_players_device_is_deleted_from_the_registry(hass: HomeAssistant):
    # Given
    entry = config_entry_for()
    entry.add_to_hass(hass)
    device_id = add_player_device(hass, entry, PREVIOUS_PROFILE_ID)

    # When
    remove_previous_players_devices(hass, entry)

    # Then
    assert device_registry.async_get(hass).async_get(device_id) is None
