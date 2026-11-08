from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from custom_components.aoe2.const import DOMAIN
from custom_components.aoe2.ha._coordinator import Aoe2Coordinator
from custom_components.aoe2.ha._identifiers import get_player_unique_id


class Aoe2Entity(CoordinatorEntity[Aoe2Coordinator]):
    _attr_has_entity_name: bool = True

    def __init__(
        self,
        coordinator: Aoe2Coordinator,
        translation_key: str,
        unique_id_suffix: str | None = None,
    ) -> None:
        super().__init__(coordinator)
        profile_id = coordinator.profile_id
        self._attr_translation_key: str = translation_key
        self._attr_unique_id: str = f"{profile_id}_{unique_id_suffix or translation_key}"
        self._attr_attribution: str = coordinator.client.attribution
        self._attr_device_info: DeviceInfo = DeviceInfo(
            identifiers={(DOMAIN, get_player_unique_id(profile_id))},
            name=coordinator.data.profile.name,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=coordinator.client.profile_url(profile_id),
        )
