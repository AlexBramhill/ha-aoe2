import logging

from .api import ClientName

DOMAIN = "aoe2"
LOGGER = logging.getLogger(__package__)

CONF_CLIENT = "client"
CONF_PROFILE_ID = "profile_id"

DEFAULT_CLIENT: ClientName = "aoe2companion"

EVENT_MATCH_FINISHED = f"{DOMAIN}_match_finished"

ATTRIBUTION = "Data provided by aoe2companion.com"
