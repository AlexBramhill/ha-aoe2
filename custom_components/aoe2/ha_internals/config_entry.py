from homeassistant.config_entries import ConfigEntry

from custom_components.aoe2.ha_internals.coordinator import Aoe2Coordinator

type Aoe2ConfigEntry = ConfigEntry[Aoe2Coordinator]
