from homeassistant.core import HomeAssistant

from custom_components.aoe2.const import CONF_PROFILE_ID
from custom_components.aoe2.ha_internals.coordinator import Aoe2ConfigEntry
from custom_components.aoe2.ha_internals.recorded_matches import RecordedMatches
from custom_components.aoe2.ha_internals.setup import PLATFORMS, async_set_up_player


async def async_setup_entry(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> bool:
    return await async_set_up_player(hass, config_entry)


async def async_unload_entry(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> None:
    await RecordedMatches(
        hass, config_entry.entry_id, config_entry.data[CONF_PROFILE_ID]
    ).async_remove()
