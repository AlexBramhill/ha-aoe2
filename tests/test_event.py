from datetime import timedelta

import pytest
from homeassistant.const import STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant

from custom_components.aoe2.const import EVENT_MATCH_FINISHED
from tests.api.builders import TYPICAL_START, MatchBuilder
from tests.fake_client import FakeAoeClient
from tests.integration import refresh, set_up_integration, state_of

OTHER_PROFILE_ID = 999

FIRST_MATCH = MatchBuilder().with_match_id(1)
NEXT_MATCH = MatchBuilder().with_match_id(2).with_start(TYPICAL_START + timedelta(hours=1))


@pytest.mark.usefixtures("created_client_names")
async def test_match_finished_has_not_fired_after_setup(hass: HomeAssistant):
    # When
    await set_up_integration(hass)

    # Then
    assert state_of(hass, Platform.EVENT, "match_finished").state == STATE_UNKNOWN


@pytest.mark.usefixtures("created_client_names")
async def test_match_finished_fires_for_newly_finished_match(
    hass: HomeAssistant, fake_client: FakeAoeClient
):
    # Given
    entry = await set_up_integration(hass)
    fake_client.matches = [NEXT_MATCH.build(), FIRST_MATCH.build()]

    # When
    await refresh(hass, entry)

    # Then
    match_finished = state_of(hass, Platform.EVENT, "match_finished")
    assert match_finished.state != STATE_UNKNOWN
    assert match_finished.attributes["event_type"] == "win"
    assert match_finished.attributes["match_id"] == 2


@pytest.mark.usefixtures("created_client_names")
async def test_match_finished_ignores_other_players(hass: HomeAssistant):
    # Given
    await set_up_integration(hass)

    # When
    hass.bus.async_fire(EVENT_MATCH_FINISHED, {"profile_id": OTHER_PROFILE_ID, "won": True})
    await hass.async_block_till_done()

    # Then
    assert state_of(hass, Platform.EVENT, "match_finished").state == STATE_UNKNOWN
