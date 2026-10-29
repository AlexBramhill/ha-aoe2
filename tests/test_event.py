from datetime import timedelta

import pytest
from homeassistant.const import STATE_UNKNOWN, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import EventStateChangedData, async_track_state_change_event

from custom_components.aoe2.const import EVENT_MATCH_FINISHED
from custom_components.aoe2.models import Leaderboard
from tests.builders import TYPICAL_START, MatchBuilder, ProfileBuilder, build_rating
from tests.fake_client import FakeAoeClient
from tests.integration import refresh, set_up_integration, state_of

RATING_AFTER_NEXT_MATCH = 1700

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
async def test_sensors_are_updated_before_match_finished_entity_fires(
    hass: HomeAssistant, fake_client: FakeAoeClient
):
    # Given
    entry = await set_up_integration(hass)
    ratings_seen_at_event: list[str] = []

    @callback
    def record_rating(_event: Event[EventStateChangedData]) -> None:
        ratings_seen_at_event.append(state_of(hass, Platform.SENSOR, "rm_1v1_rating").state)

    match_finished = state_of(hass, Platform.EVENT, "match_finished").entity_id
    async_track_state_change_event(hass, match_finished, record_rating)
    fake_client.profile = (
        ProfileBuilder()
        .with_rating(build_rating(Leaderboard.RM_1V1, RATING_AFTER_NEXT_MATCH))
        .build()
        .expected
    )
    fake_client.matches = [NEXT_MATCH.build(), FIRST_MATCH.build()]

    # When
    await refresh(hass, entry)

    # Then
    assert ratings_seen_at_event == [str(RATING_AFTER_NEXT_MATCH)]


@pytest.mark.usefixtures("created_client_names")
async def test_sensors_are_updated_before_match_finished_fires(
    hass: HomeAssistant, fake_client: FakeAoeClient
):
    # Given
    entry = await set_up_integration(hass)
    ratings_seen_at_event: list[str] = []

    @callback
    def record_rating(_event: Event) -> None:
        ratings_seen_at_event.append(state_of(hass, Platform.SENSOR, "rm_1v1_rating").state)

    hass.bus.async_listen(EVENT_MATCH_FINISHED, record_rating)
    fake_client.profile = (
        ProfileBuilder()
        .with_rating(build_rating(Leaderboard.RM_1V1, RATING_AFTER_NEXT_MATCH))
        .build()
        .expected
    )
    fake_client.matches = [NEXT_MATCH.build(), FIRST_MATCH.build()]

    # When
    await refresh(hass, entry)

    # Then
    assert ratings_seen_at_event == [str(RATING_AFTER_NEXT_MATCH)]
