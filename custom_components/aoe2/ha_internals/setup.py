from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.aoe2.api import BACKGROUND_REQUESTS
from custom_components.aoe2.const import CONF_CLIENT
from custom_components.aoe2.ha_internals.client import async_create_client
from custom_components.aoe2.ha_internals.coordinator import Aoe2ConfigEntry, Aoe2Coordinator
from custom_components.aoe2.ha_internals.devices import remove_previous_players_devices

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.EVENT, Platform.SENSOR]


async def async_set_up_player(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> bool:
    client = await async_create_client(hass, config_entry.data[CONF_CLIENT], BACKGROUND_REQUESTS)
    coordinator = Aoe2Coordinator(hass, config_entry, client)
    await coordinator.async_config_entry_first_refresh()
    config_entry.runtime_data = coordinator
    remove_previous_players_devices(hass, config_entry)
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True
