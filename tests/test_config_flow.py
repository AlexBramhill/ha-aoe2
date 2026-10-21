import json
from pathlib import Path

import pytest
from homeassistant.config_entries import SOURCE_USER, ConfigFlowResult
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
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
from custom_components.aoe2.const import CONF_CLIENT, CONF_PROFILE_ID, DEFAULT_CLIENT, DOMAIN
from tests.fake_client import FakeAoeClient

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
