import json

import pytest
from homeassistant.components.diagnostics import REDACTED
from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import JSONEncoder

from custom_components.aoe2.diagnostics import async_get_config_entry_diagnostics
from tests.fake_client import FakeAoeClient
from tests.integration import set_up_integration
from tests.json_values import get_at, get_list_at


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
    assert get_at(diagnostics, "data", "profile", "profile_id") == REDACTED
    assert get_at(diagnostics, "entry", "data", "profile_id") == REDACTED
    assert get_at(diagnostics, "data", "matches_newest_first", 0, "match_id") == REDACTED
    players = get_list_at(diagnostics, "data", "matches_newest_first", 0, "players")
    assert all(get_at(player, "name") == REDACTED for player in players)


@pytest.mark.usefixtures("created_client_names")
async def test_diagnostics_keep_details_useful_for_debugging(hass: HomeAssistant):
    # Given
    entry = await set_up_integration(hass)

    # When
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    # Then
    assert get_at(diagnostics, "data", "profile", "ratings", 0, "rating") == 1650
    assert get_at(diagnostics, "data", "matches_newest_first", 0, "map_name") == "Arabia"
    assert get_at(diagnostics, "coordinator", "last_update_success") is True
    assert get_at(diagnostics, "coordinator", "update_interval_seconds") == 600
