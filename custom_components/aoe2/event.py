from collections.abc import Mapping
from typing import Any

from homeassistant.components.event import EventEntity
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from custom_components.aoe2.const import EVENT_MATCH_FINISHED
from custom_components.aoe2.ha.config_entry import Aoe2ConfigEntry
from custom_components.aoe2.ha.coordinator import Aoe2Coordinator
from custom_components.aoe2.ha.entity import Aoe2Entity
from custom_components.aoe2.models import MatchResult

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Aoe2ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([Aoe2MatchFinishedEvent(entry.runtime_data)])


class Aoe2MatchFinishedEvent(Aoe2Entity, EventEntity):
    _attr_translation_key = "match_finished"

    def __init__(self, coordinator: Aoe2Coordinator) -> None:
        super().__init__(coordinator, "match_finished")
        self._attr_event_types = list(MatchResult)

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_MATCH_FINISHED, self._handle_match_finished)
        )

    @callback
    def _handle_match_finished(self, event: Event[Mapping[str, Any]]) -> None:
        if event.data["profile_id"] != self.coordinator.profile_id:
            return
        self._trigger_event(MatchResult.from_is_winner(event.data["won"]), dict(event.data))
        self.async_write_ha_state()
