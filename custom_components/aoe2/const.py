import logging

from .api import ClientName

DOMAIN = "aoe2"
LOGGER = logging.getLogger(__package__)

CONF_CLIENT = "client"
CONF_PROFILE_ID = "profile_id"

DEFAULT_CLIENT: ClientName = "aoe2companion"

CONF_UPDATE_MINUTES = "update_minutes"
CONF_IN_MATCH_UPDATE_MINUTES = "in_match_update_minutes"
MIN_UPDATE_MINUTES = 10
MIN_IN_MATCH_UPDATE_MINUTES = 3

EVENT_MATCH_FINISHED = f"{DOMAIN}_match_finished"
