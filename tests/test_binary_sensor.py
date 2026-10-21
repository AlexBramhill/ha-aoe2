import pytest
from homeassistant.const import STATE_OFF, STATE_ON, Platform
from homeassistant.core import HomeAssistant

from tests.api.builders import MatchBuilder
from tests.fake_client import FakeAoeClient
from tests.integration import refresh, set_up_integration, state_of


@pytest.mark.usefixtures("created_client_names")
async def test_in_match_is_off_when_all_matches_finished(hass: HomeAssistant):
    # When
    await set_up_integration(hass)

    # Then
    assert state_of(hass, Platform.BINARY_SENSOR, "in_match").state == STATE_OFF


@pytest.mark.usefixtures("created_client_names")
async def test_in_match_turns_on_during_unfinished_match(
    hass: HomeAssistant, fake_client: FakeAoeClient
):
    # Given
    entry = await set_up_integration(hass)
    fake_client.matches = [MatchBuilder().with_match_id(2).unfinished().build()]

    # When
    await refresh(hass, entry)

    # Then
    in_match = state_of(hass, Platform.BINARY_SENSOR, "in_match")
    assert in_match.state == STATE_ON
    assert in_match.attributes["map"] == "Arabia"
