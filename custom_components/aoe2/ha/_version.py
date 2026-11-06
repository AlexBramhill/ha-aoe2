from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from custom_components.aoe2.const import DOMAIN


async def async_get_version(hass: HomeAssistant) -> str:
    integration = await async_get_integration(hass, DOMAIN)
    return str(integration.version)
