from typing import final

from homeassistant.core import HomeAssistant

from custom_components.aoe2.ha._ledger_store import LedgerStore
from custom_components.aoe2.logic import MatchLedger, get_newly_finished_matches
from custom_components.aoe2.models import Match, PlayerData


@final
class MatchTracker:
    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store = LedgerStore(hass, entry_id)
        self._ledger: MatchLedger | None = None

    async def async_load(self) -> None:
        self._ledger = await self._store.async_load()

    async def async_take_newly_finished(self, data: PlayerData) -> list[Match]:
        newly_finished, ledger = get_newly_finished_matches(data, self._ledger)
        if ledger != self._ledger:
            await self._store.async_save(ledger)
        self._ledger = ledger
        return newly_finished

    async def async_remove(self) -> None:
        await self._store.async_remove()
