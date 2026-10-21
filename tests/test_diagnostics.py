import json

import pytest
from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import JSONEncoder

from custom_components.aoe2.diagnostics import async_get_config_entry_diagnostics
from tests.fake_client import FakeAoeClient
from tests.integration import set_up_integration


@pytest.mark.usefixtures("created_client_names")
async def test_diagnostics_redact_identifying_details(
    hass: HomeAssistant, fake_client: FakeAoeClient
):
    # Given
    entry = await set_up_integration(hass)

    # When
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    # Then
    as_text = json.dumps(diagnostics, cls=JSONEncoder)
    assert fake_client.profile.name not in as_text
    assert diagnostics["data"]["profile"]["profile_id"] == REDACTED
    assert diagnostics["entry"]["data"]["profile_id"] == REDACTED
    assert diagnostics["data"]["matches"][0]["match_id"] == REDACTED
    assert all(
        player["name"] == REDACTED for player in diagnostics["data"]["matches"][0]["players"]
    )


@pytest.mark.usefixtures("created_client_names")
async def test_diagnostics_keep_details_useful_for_debugging(hass: HomeAssistant):
    # Given
    entry = await set_up_integration(hass)

    # When
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    # Then
    first_rating = diagnostics["data"]["profile"]["ratings"][0]
    assert first_rating["rating"] == 1650
    assert diagnostics["data"]["matches"][0]["map_name"] == "Arabia"
    assert diagnostics["coordinator"]["last_update_success"] is True
    assert diagnostics["coordinator"]["update_interval_seconds"] == 600
