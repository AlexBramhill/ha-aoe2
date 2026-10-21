from homeassistant.config_entries import ConfigFlow

from .const import DOMAIN


class Aoe2ConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
