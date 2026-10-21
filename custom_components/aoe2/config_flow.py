from typing import Any

import probatio
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    AoeClient,
    AoeClientConnectionError,
    AoeClientError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    Profile,
    create_client,
)
from .const import CONF_CLIENT, CONF_PROFILE_ID, DEFAULT_CLIENT, DOMAIN, LOGGER

FORM_ERROR = "base"
ERROR_PLAYER_NOT_FOUND = "player_not_found"
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_UNKNOWN = "unknown"

POSITIVE_INTEGER = probatio.All(probatio.Coerce(int), probatio.Range(min=1))
USER_SCHEMA = probatio.Schema({probatio.Required(CONF_PROFILE_ID): POSITIVE_INTEGER})


class Aoe2ConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is None:
            return self._show_user_form()

        profile_id: int = user_input[CONF_PROFILE_ID]
        await self._abort_if_player_already_added(profile_id)

        try:
            profile = await self._get_profile(profile_id)
        except AoeClientError as error:
            return self._show_user_form(user_input, errors=_form_errors_for(error))
        return self._create_player_entry(profile_id, profile.name)

    async def _abort_if_player_already_added(self, profile_id: int) -> None:
        await self.async_set_unique_id(str(profile_id))
        self._abort_if_unique_id_configured()

    async def _get_profile(self, profile_id: int) -> Profile:
        return await self._client().get_profile(profile_id)

    def _client(self) -> AoeClient:
        return create_client(DEFAULT_CLIENT, async_get_clientsession(self.hass))

    def _create_player_entry(self, profile_id: int, player_name: str) -> ConfigFlowResult:
        return self.async_create_entry(
            title=player_name,
            data={CONF_CLIENT: DEFAULT_CLIENT, CONF_PROFILE_ID: profile_id},
        )

    def _show_user_form(
        self, user_input: dict[str, Any] | None = None, errors: dict[str, str] | None = None
    ) -> ConfigFlowResult:
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(USER_SCHEMA, user_input),
            errors=errors,
            description_placeholders={"data_source_url": self._client().website_url},
        )


def _form_errors_for(error: AoeClientError) -> dict[str, str]:
    match error:
        case AoeClientNotFoundError():
            return {CONF_PROFILE_ID: ERROR_PLAYER_NOT_FOUND}
        case AoeClientConnectionError() | AoeClientRateLimitError():
            return {FORM_ERROR: ERROR_CANNOT_CONNECT}
        case _:
            LOGGER.exception("Unexpected error checking profile")
            return {FORM_ERROR: ERROR_UNKNOWN}
