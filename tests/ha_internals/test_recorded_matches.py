from typing import Any

from homeassistant.core import HomeAssistant

from custom_components.aoe2.const import DOMAIN
from custom_components.aoe2.ha_internals.recorded_matches import RecordedMatches
from custom_components.aoe2.logic import MatchLedger

ENTRY_ID = "entry"
PROFILE_ID = 1
STORAGE_KEY = f"{DOMAIN}.{ENTRY_ID}.recorded_matches"


async def test_load_finds_nothing_for_new_entry(hass: HomeAssistant):
    # When
    loaded = await RecordedMatches(hass, ENTRY_ID).async_load()

    # Then
    assert loaded is None


async def test_saved_ledger_survives_reload(hass: HomeAssistant):
    # Given
    ledger = MatchLedger(PROFILE_ID, (1, 2))
    await RecordedMatches(hass, ENTRY_ID).async_save(ledger)

    # When
    loaded = await RecordedMatches(hass, ENTRY_ID).async_load()

    # Then
    assert loaded == ledger


async def test_saved_format_is_unchanged(hass: HomeAssistant, hass_storage: dict[str, Any]):
    # When
    await RecordedMatches(hass, ENTRY_ID).async_save(MatchLedger(PROFILE_ID, (1, 2)))

    # Then
    assert hass_storage[STORAGE_KEY]["data"] == {"match_ids": [1, 2], "profile_id": PROFILE_ID}


async def test_remove_deletes_saved_ledger(hass: HomeAssistant, hass_storage: dict[str, Any]):
    # Given
    recorded = RecordedMatches(hass, ENTRY_ID)
    await recorded.async_save(MatchLedger(PROFILE_ID, (1,)))

    # When
    await recorded.async_remove()

    # Then
    assert STORAGE_KEY not in hass_storage
