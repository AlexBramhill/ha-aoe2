from typing import override

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from custom_components.aoe2.ha import (
    Aoe2ConfigEntry,
    Aoe2Coordinator,
    Aoe2Entity,
    StateAttributes,
    get_current_match_details,
)

PARALLEL_UPDATES = 0


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: Aoe2ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([Aoe2InMatchSensor(entry.runtime_data)])


class Aoe2InMatchSensor(Aoe2Entity, BinarySensorEntity):
    _attr_translation_key: str = "in_match"

    def __init__(self, coordinator: Aoe2Coordinator) -> None:
        super().__init__(coordinator, self._attr_translation_key)

    @property
    @override
    def is_on(self) -> bool:
        return self.coordinator.data.is_in_current_match()

    @property
    @override
    def extra_state_attributes(self) -> StateAttributes:
        return get_current_match_details(self.coordinator.data)
