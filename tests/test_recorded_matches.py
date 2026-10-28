from typing import Any

from homeassistant.core import HomeAssistant

from custom_components.aoe2.const import DOMAIN
from custom_components.aoe2.ha_internals.recorded_matches import MAX_RECORDED_MATCHES, RecordedMatches

ENTRY_ID = "entry"
PROFILE_ID = 1
OTHER_PROFILE_ID = 2
STORAGE_KEY = f"{DOMAIN}.{ENTRY_ID}.recorded_matches"


async def loaded(hass: HomeAssistant, profile_id: int = PROFILE_ID) -> RecordedMatches:
    recorded = RecordedMatches(hass, ENTRY_ID, profile_id)
    await recorded.async_load()
    return recorded


async def test_load_reports_nothing_saved_for_new_entry(hass: HomeAssistant):
    # Given
    recorded = RecordedMatches(hass, ENTRY_ID, PROFILE_ID)

    # When
    found = await recorded.async_load()

    # Then
    assert not found


async def test_recorded_ids_survive_reload(hass: HomeAssistant):
    # Given
    await (await loaded(hass)).async_record([1, 2])

    # When
    reloaded = await loaded(hass)

    # Then
    assert 1 in reloaded
    assert 2 in reloaded
    assert 3 not in reloaded


async def test_only_most_recent_ids_are_kept(hass: HomeAssistant):
    # Given
    recorded = await loaded(hass)
    oldest_kept = 6

    # When
    await recorded.async_record(range(1, MAX_RECORDED_MATCHES + oldest_kept))

    # Then
    assert oldest_kept - 1 not in recorded
    assert oldest_kept in recorded


async def test_recording_an_id_twice_saves_one_copy(
    hass: HomeAssistant, hass_storage: dict[str, Any]
):
    # Given
    recorded = await loaded(hass)
    await recorded.async_record([1])

    # When
    await recorded.async_record([1])

    # Then
    assert hass_storage[STORAGE_KEY]["data"] == {"match_ids": [1], "profile_id": PROFILE_ID}


async def test_ids_recorded_for_another_player_are_not_loaded(hass: HomeAssistant):
    # Given
    await (await loaded(hass, OTHER_PROFILE_ID)).async_record([1])
    recorded = RecordedMatches(hass, ENTRY_ID, PROFILE_ID)

    # When
    found = await recorded.async_load()

    # Then
    assert not found
    assert 1 not in recorded
