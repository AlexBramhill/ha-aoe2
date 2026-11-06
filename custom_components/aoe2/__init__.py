from homeassistant.core import HomeAssistant

from custom_components.aoe2.ha import PLATFORMS, Aoe2ConfigEntry, MatchTracker, async_set_up_player


async def async_setup_entry(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> bool:
    return await async_set_up_player(hass, config_entry)


async def async_unload_entry(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> None:
    await MatchTracker(hass, config_entry.entry_id).async_remove()
