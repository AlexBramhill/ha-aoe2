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

from custom_components.aoe2.api import (
    INTERACTIVE_REQUESTS,
    AoeClient,
    AoeClientError,
    AoeClientNotFoundError,
    AoeClientRetryError,
    Profile,
    create_client,
)
from custom_components.aoe2.const import (
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
from custom_components.aoe2.ha_internals.user_agent import async_user_agent

FORM_ERROR = "base"
ERROR_PLAYER_NOT_FOUND = "player_not_found"
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_UNKNOWN = "unknown"

POSITIVE_INTEGER = probatio.All(probatio.Coerce(int), probatio.Range(min=1))

PROFILE_SCHEMA = probatio.Schema({probatio.Required(CONF_PROFILE_ID): POSITIVE_INTEGER})


def _get_minutes_selector(minimum: int) -> NumberSelector:
    return NumberSelector(
        NumberSelectorConfig(
            min=minimum, step=1, unit_of_measurement="min", mode=NumberSelectorMode.BOX
        )
    )


OPTIONS_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_UPDATE_MINUTES, default=MIN_UPDATE_MINUTES): _get_minutes_selector(
            MIN_UPDATE_MINUTES
        ),
        probatio.Required(
            CONF_IN_MATCH_UPDATE_MINUTES, default=MIN_IN_MATCH_UPDATE_MINUTES
        ): _get_minutes_selector(MIN_IN_MATCH_UPDATE_MINUTES),
    }
)

MINIMUM_INTERVAL_PLACEHOLDERS = {
    "min_update_minutes": str(MIN_UPDATE_MINUTES),
    "min_in_match_update_minutes": str(MIN_IN_MATCH_UPDATE_MINUTES),
}


class Aoe2ConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> Aoe2OptionsFlow:
        return Aoe2OptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        client = await self._get_client()
        if user_input is None:
            return self._show_profile_form("user", client)

        profile_id: int = user_input[CONF_PROFILE_ID]
        await self._abort_if_player_already_added(profile_id)

        match await _get_profile_or_form_errors(client, profile_id):
            case Profile() as profile:
                return self._create_player_entry(profile_id, profile.name)
            case errors:
                return self._show_profile_form("user", client, user_input, errors)

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        client = await self._get_client()
        if user_input is None:
            return self._show_profile_form("reconfigure", client, dict(entry.data))

        profile_id: int = user_input[CONF_PROFILE_ID]
        is_new_player = profile_id != entry.data[CONF_PROFILE_ID]
        if is_new_player:
            await self._abort_if_player_already_added(profile_id)

        match await _get_profile_or_form_errors(client, profile_id):
            case Profile() as profile:
                return self._update_player_entry(entry, profile_id, profile.name)
            case errors:
                return self._show_profile_form("reconfigure", client, user_input, errors)

    async def _abort_if_player_already_added(self, profile_id: int) -> None:
        await self.async_set_unique_id(str(profile_id))
        self._abort_if_unique_id_configured()

    def _create_player_entry(self, profile_id: int, player_name: str) -> ConfigFlowResult:
        return self.async_create_entry(
            title=player_name,
            data={CONF_CLIENT: DEFAULT_CLIENT, CONF_PROFILE_ID: profile_id},
        )

    async def _get_client(self) -> AoeClient:
        return create_client(
            DEFAULT_CLIENT,
            async_get_clientsession(self.hass),
            await async_user_agent(self.hass),
            INTERACTIVE_REQUESTS,
        )

    def _show_profile_form(
        self,
        step_id: str,
        client: AoeClient,
        suggested_values: dict[str, Any] | None = None,
        errors: dict[str, str] | None = None,
    ) -> ConfigFlowResult:
        return self.async_show_form(
            step_id=step_id,
            data_schema=self.add_suggested_values_to_schema(PROFILE_SCHEMA, suggested_values),
            errors=errors,
            description_placeholders={"data_source_url": client.website_url},
        )

    def _update_player_entry(
        self, entry: ConfigEntry, profile_id: int, player_name: str
    ) -> ConfigFlowResult:
        return self.async_update_reload_and_abort(
            entry,
            unique_id=str(profile_id),
            title=player_name,
            data_updates={CONF_PROFILE_ID: profile_id},
        )


class Aoe2OptionsFlow(OptionsFlowWithReload):
    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(data=_get_whole_minutes(user_input))
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
            description_placeholders=MINIMUM_INTERVAL_PLACEHOLDERS,
        )


def _get_whole_minutes(options: dict[str, Any]) -> dict[str, int]:
    return {key: int(minutes) for key, minutes in options.items()}


async def _get_profile_or_form_errors(
    client: AoeClient, profile_id: int
) -> Profile | dict[str, str]:
    try:
        return await client.get_profile(profile_id)
    except AoeClientNotFoundError:
        return {CONF_PROFILE_ID: ERROR_PLAYER_NOT_FOUND}
    except AoeClientRetryError:
        return {FORM_ERROR: ERROR_CANNOT_CONNECT}
    except AoeClientError:
        LOGGER.exception("Unexpected error checking profile")
        return {FORM_ERROR: ERROR_UNKNOWN}
