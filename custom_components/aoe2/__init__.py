from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import BACKGROUND_REQUESTS, create_client
from .const import CONF_CLIENT, CONF_PROFILE_ID, DOMAIN
from .coordinator import Aoe2ConfigEntry, Aoe2Coordinator
from .recorded_matches import RecordedMatches
from .user_agent import async_user_agent

PLATFORMS: list[Platform] = [Platform.BINARY_SENSOR, Platform.EVENT, Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> bool:
    client = create_client(
        config_entry.data[CONF_CLIENT],
        async_get_clientsession(hass),
        await async_user_agent(hass),
        BACKGROUND_REQUESTS,
    )
    coordinator = Aoe2Coordinator(hass, config_entry, client)
    await coordinator.async_config_entry_first_refresh()
    config_entry.runtime_data = coordinator
    _remove_previous_players_devices(hass, config_entry)
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> None:
    await RecordedMatches(hass, config_entry.entry_id, config_entry.data[CONF_PROFILE_ID]).async_remove()


@callback
def _remove_previous_players_devices(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> None:
    devices = device_registry.async_get(hass)
    current_player = (DOMAIN, str(config_entry.data[CONF_PROFILE_ID]))
    for device in device_registry.async_entries_for_config_entry(devices, config_entry.entry_id):
        if current_player not in device.identifiers:
            devices.async_update_device(device.id, remove_config_entry_id=config_entry.entry_id)
