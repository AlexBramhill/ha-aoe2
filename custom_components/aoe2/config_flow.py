from collections.abc import Mapping
from typing import final, override

import probatio
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    Selector,
)

from custom_components.aoe2.api import (
    INTERACTIVE_REQUESTS,
    AoeClient,
    AoeClientError,
    AoeClientNotFoundError,
    AoeClientRetryableError,
)
from custom_components.aoe2.const import (
    CONF_IN_MATCH_UPDATE_MINUTES,
    CONF_PROFILE_ID,
    CONF_UPDATE_MINUTES,
    DEFAULT_CLIENT,
    DOMAIN,
    LOGGER,
    MIN_IN_MATCH_UPDATE_MINUTES,
    MIN_UPDATE_MINUTES,
)
from custom_components.aoe2.ha import EntryData, EntryOptions, async_create_client
from custom_components.aoe2.models import Profile

FORM_ERROR = "base"
ERROR_PLAYER_NOT_FOUND = "player_not_found"
ERROR_CANNOT_CONNECT = "cannot_connect"
ERROR_UNKNOWN = "unknown"

POSITIVE_INTEGER = probatio.All(probatio.Coerce(int), probatio.Range(min=1))

PROFILE_SCHEMA = probatio.Schema({probatio.Required(CONF_PROFILE_ID): POSITIVE_INTEGER})


def _get_minutes_selector(minimum: int) -> Selector[NumberSelectorConfig]:
    # HA's selector registry erases NumberSelector's type argument
    return NumberSelector(  # pyright: ignore[reportUnknownVariableType]
        NumberSelectorConfig(
            min=minimum, step=1, unit_of_measurement="min", mode=NumberSelectorMode.BOX
        )
    )


MINIMUM_MINUTES = {
    CONF_UPDATE_MINUTES: MIN_UPDATE_MINUTES,
    CONF_IN_MATCH_UPDATE_MINUTES: MIN_IN_MATCH_UPDATE_MINUTES,
}

OPTIONS_SCHEMA = probatio.Schema(
    {
        probatio.Required(key, default=minimum): _get_minutes_selector(minimum)
        for key, minimum in MINIMUM_MINUTES.items()
    }
)

MINIMUM_INTERVAL_PLACEHOLDERS = {
    "min_update_minutes": str(MIN_UPDATE_MINUTES),
    "min_in_match_update_minutes": str(MIN_IN_MATCH_UPDATE_MINUTES),
}


@final
class Aoe2ConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    @staticmethod
    @callback
    @override
    def async_get_options_flow(config_entry: ConfigEntry) -> Aoe2OptionsFlow:
        return Aoe2OptionsFlow()

    @override
    async def async_step_user(
        self, user_input: dict[str, object] | None = None
    ) -> ConfigFlowResult:
        client = await self._get_client()
        if user_input is None:
            return self._show_profile_form("user", client)

        profile_id = _get_profile_id(user_input)
        await self._abort_if_player_already_added(profile_id)

        match await _get_profile_or_form_errors(client, profile_id):
            case Profile() as profile:
                return self._create_player_entry(profile_id, profile.name)
            case errors:
                return self._show_profile_form("user", client, user_input, errors)

    async def async_step_reconfigure(
        self, user_input: dict[str, object] | None = None
    ) -> ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        client = await self._get_client()
        if user_input is None:
            return self._show_profile_form("reconfigure", client, dict(entry.data))

        profile_id = _get_profile_id(user_input)
        is_new_player = str(profile_id) != entry.unique_id
        if is_new_player:
            await self._abort_if_player_already_added(profile_id)

        match await _get_profile_or_form_errors(client, profile_id):
            case Profile() as profile:
                return self._update_player_entry(entry, profile_id, profile.name)
            case errors:
                return self._show_profile_form("reconfigure", client, user_input, errors)

    async def _abort_if_player_already_added(self, profile_id: int) -> None:
        _ = await self.async_set_unique_id(str(profile_id))
        self._abort_if_unique_id_configured()

    def _create_player_entry(self, profile_id: int, player_name: str) -> ConfigFlowResult:
        return self.async_create_entry(
            title=player_name,
            data=EntryData(profile_id=profile_id).model_dump(mode="json"),
        )

    async def _get_client(self) -> AoeClient:
        return await async_create_client(self.hass, DEFAULT_CLIENT, INTERACTIVE_REQUESTS)

    def _show_profile_form(
        self,
        step_id: str,
        client: AoeClient,
        suggested_values: Mapping[str, object] | None = None,
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
            data=EntryData.from_entry(entry).with_profile_id(profile_id).model_dump(mode="json"),
        )


class Aoe2OptionsFlow(OptionsFlowWithReload):
    async def async_step_init(
        self, user_input: dict[str, object] | None = None
    ) -> ConfigFlowResult:
        if user_input is not None:
            return self.async_create_entry(
                data=_get_options_from(user_input).model_dump(mode="json")
            )
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
            description_placeholders=MINIMUM_INTERVAL_PLACEHOLDERS,
        )


def _get_profile_id(user_input: Mapping[str, object]) -> int:
    profile_id = user_input[CONF_PROFILE_ID]
    assert isinstance(profile_id, int)
    return profile_id


def _get_options_from(user_input: dict[str, object]) -> EntryOptions:
    """Number selectors hand back floats even with a step of 1, so whole floats are allowed."""
    return EntryOptions.model_validate(user_input, strict=False)


async def _get_profile_or_form_errors(
    client: AoeClient, profile_id: int
) -> Profile | dict[str, str]:
    try:
        return await client.get_profile(profile_id)
    except AoeClientNotFoundError:
        return {CONF_PROFILE_ID: ERROR_PLAYER_NOT_FOUND}
    except AoeClientRetryableError:
        return {FORM_ERROR: ERROR_CANNOT_CONNECT}
    except AoeClientError:
        LOGGER.exception("Unexpected error checking profile")
        return {FORM_ERROR: ERROR_UNKNOWN}
