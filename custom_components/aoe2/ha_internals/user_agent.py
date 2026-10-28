from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from custom_components.aoe2.const import DOMAIN


async def async_user_agent(hass: HomeAssistant) -> str:
    integration = await async_get_integration(hass, DOMAIN)
    return f"ha-aoe2/{integration.version} (+https://github.com/AlexBramhill/ha-aoe2)"
