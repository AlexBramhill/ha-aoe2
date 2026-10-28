import json
from pathlib import Path

from homeassistant.core import HomeAssistant

from custom_components.aoe2.ha_internals.user_agent import async_get_user_agent

MANIFEST = Path(__file__).parents[1] / "custom_components/aoe2/manifest.json"


async def test_user_agent_names_the_manifest_version_and_project(hass: HomeAssistant):
    # Given
    version = json.loads(MANIFEST.read_text())["version"]

    # When
    user_agent = await async_get_user_agent(hass)

    # Then
    assert user_agent == f"ha-aoe2/{version} (+https://github.com/AlexBramhill/ha-aoe2)"
