from typing import TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from custom_components.aoe2.const import DOMAIN
from custom_components.aoe2.logic import MatchLedger

STORAGE_VERSION = 1


class StoredRecordedMatches(TypedDict):
    match_ids: list[int]
    profile_id: int


class RecordedMatches:
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store = Store[StoredRecordedMatches](
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.recorded_matches"
        )

    async def async_load(self) -> MatchLedger | None:
        stored = await self._store.async_load()
        if stored is None:
            return None
        return MatchLedger(profile_id=stored["profile_id"], match_ids=tuple(stored["match_ids"]))

    async def async_save(self, ledger: MatchLedger) -> None:
        await self._store.async_save(
            StoredRecordedMatches(match_ids=list(ledger.match_ids), profile_id=ledger.profile_id)
        )

    async def async_remove(self) -> None:
        await self._store.async_remove()
