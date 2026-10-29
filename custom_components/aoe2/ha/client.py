from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.aoe2.api import AoeClient, ClientName, RequestPolicy, create_client
from custom_components.aoe2.ha.version import async_get_version


async def async_create_client(
    hass: HomeAssistant, client_name: ClientName, policy: RequestPolicy
) -> AoeClient:
    return create_client(
        client_name,
        async_get_clientsession(hass),
        await async_get_version(hass),
        policy,
    )
