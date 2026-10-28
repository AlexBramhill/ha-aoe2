from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry

from custom_components.aoe2.const import CONF_PROFILE_ID, DOMAIN
from custom_components.aoe2.ha_internals.config_entry import Aoe2ConfigEntry


@callback
def remove_previous_players_devices(hass: HomeAssistant, config_entry: Aoe2ConfigEntry) -> None:
    devices = device_registry.async_get(hass)
    current_player = (DOMAIN, str(config_entry.data[CONF_PROFILE_ID]))
    for device in device_registry.async_entries_for_config_entry(devices, config_entry.entry_id):
        if current_player not in device.identifiers:
            devices.async_update_device(device.id, remove_config_entry_id=config_entry.entry_id)
