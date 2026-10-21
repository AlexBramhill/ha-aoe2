from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import AoeClient, create_client
from .const import CONF_CLIENT

PLATFORMS: list[Platform] = []

type Aoe2ConfigEntry = ConfigEntry[AoeClient]


async def async_setup_entry(hass: HomeAssistant, entry: Aoe2ConfigEntry) -> bool:
    session = async_get_clientsession(hass)
    entry.runtime_data = create_client(entry.data[CONF_CLIENT], session)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: Aoe2ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
