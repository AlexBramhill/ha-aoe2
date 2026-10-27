from homeassistant.components.event import EventEntity
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import EVENT_MATCH_FINISHED
from .coordinator import Aoe2ConfigEntry, Aoe2Coordinator, MatchFinishedEventData
from .entity import Aoe2Entity

PARALLEL_UPDATES = 0

EVENT_WIN = "win"
EVENT_LOSS = "loss"
EVENT_UNKNOWN_RESULT = "unknown"


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
        self._attr_event_types = [EVENT_WIN, EVENT_LOSS, EVENT_UNKNOWN_RESULT]

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        self.async_on_remove(
            self.hass.bus.async_listen(EVENT_MATCH_FINISHED, self._handle_match_finished)
        )

    @callback
    def _handle_match_finished(self, event: Event[MatchFinishedEventData]) -> None:
        if event.data["profile_id"] != self.coordinator.profile_id:
            return
        self._trigger_event(_get_event_type(event.data["won"]), dict(event.data))
        self.async_write_ha_state()


def _get_event_type(won: bool | None) -> str:
    match won:
        case True:
            return EVENT_WIN
        case False:
            return EVENT_LOSS
        case None:
            return EVENT_UNKNOWN_RESULT
