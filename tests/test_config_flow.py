import json
from datetime import timedelta
from pathlib import Path

import pytest
from homeassistant.config_entries import SOURCE_USER, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType, InvalidData
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aoe2.api import (
    AoeClientConnectionError,
    AoeClientError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
)
from custom_components.aoe2.config_flow import (
    ERROR_CANNOT_CONNECT,
    ERROR_PLAYER_NOT_FOUND,
    ERROR_UNKNOWN,
)
from custom_components.aoe2.const import (
    CONF_CLIENT,
    CONF_IN_MATCH_UPDATE_MINUTES,
    CONF_PROFILE_ID,
    CONF_UPDATE_MINUTES,
    DEFAULT_CLIENT,
    DOMAIN,
    MIN_IN_MATCH_UPDATE_MINUTES,
    MIN_UPDATE_MINUTES,
)
from tests.fake_client import FakeAoeClient
from tests.integration import set_up_integration

PROFILE_ID = 196240
TRANSLATIONS = Path(__file__).parents[1] / "custom_components/aoe2/translations/en.json"


async def start_flow(hass: HomeAssistant) -> str:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    flow_id = result.get("flow_id")
    assert flow_id is not None
    return flow_id


async def submit_profile_id(hass: HomeAssistant, flow_id: str) -> ConfigFlowResult:
    return await hass.config_entries.flow.async_configure(
        flow_id, user_input={CONF_PROFILE_ID: PROFILE_ID}
    )


async def test_flow_starts_with_profile_id_form(hass: HomeAssistant):
    # When
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    # Then
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"


@pytest.mark.usefixtures("created_client_names")
async def test_form_links_to_the_configured_data_source(
    hass: HomeAssistant, fake_client: FakeAoeClient
):
    # When
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    # Then
    assert result.get("description_placeholders") == {"data_source_url": fake_client.website_url}


@pytest.mark.usefixtures("created_client_names")
async def test_valid_profile_creates_entry_named_after_player(
    hass: HomeAssistant, fake_client: FakeAoeClient
):
    # Given
    flow_id = await start_flow(hass)

    # When
    result = await submit_profile_id(hass, flow_id)

    # Then
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == fake_client.profile.name
    assert result.get("data") == {CONF_CLIENT: DEFAULT_CLIENT, CONF_PROFILE_ID: PROFILE_ID}
    entry = result.get("result")
    assert entry is not None
    assert entry.unique_id == str(PROFILE_ID)


@pytest.mark.usefixtures("created_client_names")
@pytest.mark.parametrize(
    ("error", "expected_errors"),
    [
        (AoeClientNotFoundError("gone"), {CONF_PROFILE_ID: "player_not_found"}),
        (AoeClientConnectionError("unreachable"), {"base": "cannot_connect"}),
        (AoeClientRateLimitError("slow down"), {"base": "cannot_connect"}),
        (AoeClientResponseError("unexpected"), {"base": "unknown"}),
    ],
    ids=["not-found", "connection", "rate-limit", "response"],
)
async def test_client_error_shows_form_with_error(
    hass: HomeAssistant,
    fake_client: FakeAoeClient,
    error: AoeClientError,
    expected_errors: dict[str, str],
):
    # Given
    fake_client.error = error
    flow_id = await start_flow(hass)

    # When
    result = await submit_profile_id(hass, flow_id)

    # Then
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == expected_errors


@pytest.mark.usefixtures("created_client_names")
async def test_form_can_be_resubmitted_after_error(hass: HomeAssistant, fake_client: FakeAoeClient):
    # Given
    fake_client.error = AoeClientConnectionError("unreachable")
    flow_id = await start_flow(hass)
    await submit_profile_id(hass, flow_id)
    fake_client.error = None

    # When
    result = await submit_profile_id(hass, flow_id)

    # Then
    assert result.get("type") is FlowResultType.CREATE_ENTRY


@pytest.mark.usefixtures("created_client_names")
async def test_already_added_player_aborts(hass: HomeAssistant):
    # Given
    MockConfigEntry(domain=DOMAIN, unique_id=str(PROFILE_ID)).add_to_hass(hass)
    flow_id = await start_flow(hass)

    # When
    result = await submit_profile_id(hass, flow_id)

    # Then
    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "already_configured"


@pytest.mark.parametrize("error_key", [ERROR_PLAYER_NOT_FOUND, ERROR_CANNOT_CONNECT, ERROR_UNKNOWN])
def test_every_form_error_has_text(error_key: str):
    # Given
    translations = json.loads(TRANSLATIONS.read_text())

    # Then
    assert error_key in translations["config"]["error"]


async def start_options_flow(hass: HomeAssistant, entry: MockConfigEntry) -> str:
    result = await hass.config_entries.options.async_init(entry.entry_id)
    flow_id = result.get("flow_id")
    assert flow_id is not None
    return flow_id


@pytest.mark.usefixtures("created_client_names")
async def test_options_save_update_intervals_and_reload(hass: HomeAssistant):
    # Given
    entry = await set_up_integration(hass)
    flow_id = await start_options_flow(hass, entry)

    # When
    result = await hass.config_entries.options.async_configure(
        flow_id, user_input={CONF_UPDATE_MINUTES: 30, CONF_IN_MATCH_UPDATE_MINUTES: 5}
    )
    await hass.async_block_till_done()

    # Then
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_UPDATE_MINUTES: 30, CONF_IN_MATCH_UPDATE_MINUTES: 5}
    assert entry.runtime_data.update_interval == timedelta(minutes=30)


@pytest.mark.usefixtures("created_client_names")
@pytest.mark.parametrize(
    "too_frequent",
    [
        {CONF_UPDATE_MINUTES: MIN_UPDATE_MINUTES - 1, CONF_IN_MATCH_UPDATE_MINUTES: 5},
        {CONF_UPDATE_MINUTES: 30, CONF_IN_MATCH_UPDATE_MINUTES: MIN_IN_MATCH_UPDATE_MINUTES - 1},
    ],
    ids=["usual", "in-match"],
)
async def test_options_reject_intervals_below_minimum(
    hass: HomeAssistant, too_frequent: dict[str, int]
):
    # Given
    entry = await set_up_integration(hass)
    flow_id = await start_options_flow(hass, entry)

    # When / Then
    with pytest.raises(InvalidData):
        await hass.config_entries.options.async_configure(flow_id, user_input=too_frequent)
