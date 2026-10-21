from typing import Any

import probatio
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from .api import (
    AoeClient,
    AoeClientConnectionError,
    AoeClientError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    Profile,
    create_client,
)
from .const import (
    CONF_CLIENT,
    CONF_IN_MATCH_UPDATE_MINUTES,
    CONF_PROFILE_ID,
    CONF_UPDATE_MINUTES,
    DEFAULT_CLIENT,
    DOMAIN,
    LOGGER,
    MIN_IN_MATCH_UPDATE_MINUTES,
    MIN_UPDATE_MINUTES,
)

FORM_ERROR = "base"
ERROR_PLAYER_NOT_FOUND = "player_not_found"
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_UNKNOWN = "unknown"

POSITIVE_INTEGER = probatio.All(probatio.Coerce(int), probatio.Range(min=1))
USER_SCHEMA = probatio.Schema({probatio.Required(CONF_PROFILE_ID): POSITIVE_INTEGER})


def _minutes_at_least(minimum: int) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=minimum, step=1, unit_of_measurement="min", mode=NumberSelectorMode.BOX
        )
    )


OPTIONS_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_UPDATE_MINUTES, default=MIN_UPDATE_MINUTES): _minutes_at_least(
            MIN_UPDATE_MINUTES
        ),
        probatio.Required(
            CONF_IN_MATCH_UPDATE_MINUTES, default=MIN_IN_MATCH_UPDATE_MINUTES
        ): _minutes_at_least(MIN_IN_MATCH_UPDATE_MINUTES),
    }
)


class Aoe2ConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> Aoe2OptionsFlow:
        return Aoe2OptionsFlow()

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


class Aoe2OptionsFlow(OptionsFlowWithReload):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=_in_whole_minutes(user_input))
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )


def _in_whole_minutes(options: dict[str, Any]) -> dict[str, int]:
    return {key: int(minutes) for key, minutes in options.items()}


def _form_errors_for(error: AoeClientError) -> dict[str, str]:
    match error:
        case AoeClientNotFoundError():
            return {CONF_PROFILE_ID: ERROR_PLAYER_NOT_FOUND}
        case AoeClientConnectionError() | AoeClientRateLimitError():
            return {FORM_ERROR: ERROR_CANNOT_CONNECT}
        case _:
            LOGGER.exception("Unexpected error checking profile")
            return {FORM_ERROR: ERROR_UNKNOWN}
