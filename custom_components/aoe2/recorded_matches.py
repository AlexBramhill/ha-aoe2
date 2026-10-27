from collections.abc import Iterable
from typing import TypedDict

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import DOMAIN

STORAGE_VERSION = 1
MAX_RECORDED_MATCHES = 1000


class StoredRecordedMatches(TypedDict):
    match_ids: list[int]
    profile_id: int


class RecordedMatches:
    def __init__(self, hass: HomeAssistant, entry_id: str, profile_id: int) -> None:
        self._store = Store[StoredRecordedMatches](
            hass, STORAGE_VERSION, f"{DOMAIN}.{entry_id}.recorded_matches"
        )
        self._profile_id = profile_id
        self._match_ids: list[int] | None = None

    @property
    def is_loaded(self) -> bool:
        return self._match_ids is not None

    async def async_load(self) -> bool:
        stored = await self._store.async_load()
        if stored is None or stored["profile_id"] != self._profile_id:
            self._match_ids = []
            return False
        self._match_ids = stored["match_ids"]
        return True

    def __contains__(self, match_id: int) -> bool:
        return match_id in self._get_loaded_match_ids()

    async def async_record(self, match_ids: Iterable[int]) -> None:
        recorded = self._get_loaded_match_ids()
        recorded.extend(match_id for match_id in match_ids if match_id not in recorded)
        del recorded[:-MAX_RECORDED_MATCHES]
        await self._store.async_save(
            StoredRecordedMatches(match_ids=recorded, profile_id=self._profile_id)
        )

    async def async_remove(self) -> None:
        await self._store.async_remove()

    def _get_loaded_match_ids(self) -> list[int]:
        if self._match_ids is None:
            raise RuntimeError("Recorded matches used before async_load")
        return self._match_ids
