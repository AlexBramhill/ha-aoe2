import pytest
from homeassistant.core import HomeAssistant

from custom_components.aoe2.api import (
    BACKGROUND_REQUESTS,
    INTERACTIVE_REQUESTS,
    AoeClient,
    ClientName,
    RequestPolicy,
)
from custom_components.aoe2.ha_internals import client
from custom_components.aoe2.ha_internals.client import async_create_client
from tests.fake_client import FakeAoeClient
from tests.ha_internals.helpers import read_manifest_version


@pytest.mark.parametrize("policy", [BACKGROUND_REQUESTS, INTERACTIVE_REQUESTS])
async def test_client_is_created_with_the_integration_version(
    hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch, policy: RequestPolicy
):
    # Given
    created: list[tuple[ClientName, str, RequestPolicy]] = []

    def recording_create_client(
        client_name: ClientName, _session: object, version: str, policy: RequestPolicy
    ) -> AoeClient:
        created.append((client_name, version, policy))
        return FakeAoeClient()

    monkeypatch.setattr(client, "create_client", recording_create_client)

    # When
    await async_create_client(hass, "aoe2companion", policy)

    # Then
    assert created == [("aoe2companion", read_manifest_version(), policy)]
