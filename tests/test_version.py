import json
from pathlib import Path

from homeassistant.core import HomeAssistant

from custom_components.aoe2.ha_internals.version import async_get_version

MANIFEST = Path(__file__).parents[1] / "custom_components/aoe2/manifest.json"


async def test_version_is_the_manifest_version(hass: HomeAssistant):
    # Given
    manifest_version = json.loads(MANIFEST.read_text())["version"]

    # When
    version = await async_get_version(hass)

    # Then
    assert version == manifest_version
