from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant

from custom_components.aoe2.const import DOMAIN
from custom_components.aoe2.ha._match_tracker import MatchTracker
from custom_components.aoe2.models import PlayerData
from tests.builders import TYPICAL_START, MatchBuilder, ProfileBuilder

ENTRY_ID = "entry"
STORAGE_KEY = f"{DOMAIN}.{ENTRY_ID}.recorded_matches"
PLAYER = ProfileBuilder().build().expected
FIRST_MATCH = MatchBuilder().with_match_id(1).build()
NEXT_MATCH = MatchBuilder().with_match_id(2).with_start(TYPICAL_START + timedelta(hours=1)).build()

BEFORE_NEXT_MATCH = PlayerData(profile=PLAYER, unsorted_matches=[FIRST_MATCH])
AFTER_NEXT_MATCH = PlayerData(profile=PLAYER, unsorted_matches=[NEXT_MATCH, FIRST_MATCH])


async def loaded_tracker(hass: HomeAssistant) -> MatchTracker:
    tracker = MatchTracker(hass, ENTRY_ID)
    await tracker.async_load()
    return tracker


async def test_matches_finished_before_tracking_started_are_not_returned(hass: HomeAssistant):
    # Given
    tracker = await loaded_tracker(hass)

    # When
    taken = await tracker.async_take_newly_finished(BEFORE_NEXT_MATCH)

    # Then
    assert taken == []


async def test_newly_finished_match_is_returned_only_once(hass: HomeAssistant):
    # Given
    tracker = await loaded_tracker(hass)
    await tracker.async_take_newly_finished(BEFORE_NEXT_MATCH)

    # When
    first_take = await tracker.async_take_newly_finished(AFTER_NEXT_MATCH)
    second_take = await tracker.async_take_newly_finished(AFTER_NEXT_MATCH)

    # Then
    assert first_take == [NEXT_MATCH]
    assert second_take == []


async def test_returned_match_is_not_returned_again_after_restart(hass: HomeAssistant):
    # Given
    before_restart = await loaded_tracker(hass)
    await before_restart.async_take_newly_finished(BEFORE_NEXT_MATCH)
    await before_restart.async_take_newly_finished(AFTER_NEXT_MATCH)

    # When
    after_restart = await loaded_tracker(hass)
    taken = await after_restart.async_take_newly_finished(AFTER_NEXT_MATCH)

    # Then
    assert taken == []


async def test_match_that_finished_while_stopped_is_returned_after_restart(hass: HomeAssistant):
    # Given
    before_restart = await loaded_tracker(hass)
    await before_restart.async_take_newly_finished(BEFORE_NEXT_MATCH)

    # When
    after_restart = await loaded_tracker(hass)
    taken = await after_restart.async_take_newly_finished(AFTER_NEXT_MATCH)

    # Then
    assert taken == [NEXT_MATCH]


async def test_remove_deletes_saved_ledger(hass: HomeAssistant, hass_storage: dict[str, Any]):
    # Given
    tracker = await loaded_tracker(hass)
    await tracker.async_take_newly_finished(BEFORE_NEXT_MATCH)
    assert STORAGE_KEY in hass_storage

    # When
    await tracker.async_remove()

    # Then
    assert STORAGE_KEY not in hass_storage
