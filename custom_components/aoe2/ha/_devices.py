from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry

from custom_components.aoe2.const import DOMAIN
from custom_components.aoe2.ha._config_entry import Aoe2ConfigEntry
from custom_components.aoe2.ha._entry_values import EntryData


@callback
def remove_previous_players_devices(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> None:
    devices = device_registry.async_get(hass)
    current_player = (DOMAIN, str(EntryData.from_entry(config_entry).profile_id))
    for device in device_registry.async_entries_for_config_entry(devices, config_entry.entry_id):
        if current_player not in device.identifiers:
            devices.async_remove_device(device.id)
