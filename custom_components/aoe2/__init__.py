from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import create_client
from .const import CONF_CLIENT, CONF_PROFILE_ID, DOMAIN
from .coordinator import Aoe2ConfigEntry, Aoe2Coordinator
from .recorded_matches import RecordedMatches
from .user_agent import async_user_agent

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.EVENT, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: Aoe2ConfigEntry) -> bool:
    client = create_client(
        entry.data[CONF_CLIENT], async_get_clientsession(hass), await async_user_agent(hass)
    )
    coordinator = Aoe2Coordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: Aoe2ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: Aoe2ConfigEntry) -> None:
    await RecordedMatches(hass, entry.entry_id).async_remove()


async def async_forget_player(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await RecordedMatches(hass, entry.entry_id).async_remove()
    devices = device_registry.async_get(hass)
    player = (DOMAIN, str(entry.data[CONF_PROFILE_ID]))
    if device := devices.async_get_device_by_identifier(player, entry.entry_id):
        devices.async_update_device(device.id, remove_config_entry_id=entry.entry_id)
