from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from custom_components.aoe2.api import BACKGROUND_REQUESTS
from custom_components.aoe2.ha._client import async_create_client
from custom_components.aoe2.ha._config_entry import Aoe2ConfigEntry
from custom_components.aoe2.ha._coordinator import Aoe2Coordinator
from custom_components.aoe2.ha._devices import remove_previous_players_devices
from custom_components.aoe2.ha._entry_values import EntryData

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.EVENT, Platform.SENSOR]


async def async_set_up_player(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> bool:
    client = await async_create_client(
        hass, EntryData.from_entry(config_entry).client, BACKGROUND_REQUESTS
    )
    coordinator = Aoe2Coordinator(hass, config_entry, client)
    await coordinator.async_config_entry_first_refresh()
    config_entry.runtime_data = coordinator
    remove_previous_players_devices(hass, config_entry, coordinator.profile_id)
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True
