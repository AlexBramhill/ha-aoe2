from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.aoe2.const import DOMAIN
from .coordinator import Aoe2Coordinator


class Aoe2Entity(CoordinatorEntity[Aoe2Coordinator]):
    _attr_has_entity_name = True

    def __init__(self, coordinator: Aoe2Coordinator, unique_key: str) -> None:
        super().__init__(coordinator)
        profile_id = coordinator.profile_id
        self._attr_unique_id = f"{profile_id}_{unique_key}"
        self._attr_attribution = coordinator.client.attribution
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(profile_id))},
            name=coordinator.data.profile.name,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=coordinator.client.profile_url(profile_id),
        )
