from homeassistant.core import HomeAssistant

from custom_components.aoe2.ha_internals.version import async_get_version
from tests.ha_internals.helpers import read_manifest_version


async def test_version_is_the_manifest_version(hass: HomeAssistant):
    # When
    version = await async_get_version(hass)

    # Then
    assert version == read_manifest_version()
