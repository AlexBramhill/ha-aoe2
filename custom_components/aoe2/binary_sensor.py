from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from custom_components.aoe2.ha.config_entry import Aoe2ConfigEntry
from custom_components.aoe2.ha.coordinator import Aoe2Coordinator
from custom_components.aoe2.ha.entity import Aoe2Entity
from custom_components.aoe2.logic import get_current_match_details

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Aoe2ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([Aoe2InMatchSensor(entry.runtime_data)])


class Aoe2InMatchSensor(Aoe2Entity, BinarySensorEntity):
    _attr_translation_key = "in_match"

    def __init__(self, coordinator: Aoe2Coordinator) -> None:
        super().__init__(coordinator, "in_match")

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.is_in_current_match()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return get_current_match_details(self.coordinator.data)
