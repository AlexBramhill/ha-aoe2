import pytest

from custom_components.aoe2.api import AoeClient, ClientName, RequestPolicy
from custom_components.aoe2.ha_internals import client
from tests.fake_client import FakeAoeClient


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    return


@pytest.fixture
def fake_client() -> FakeAoeClient:
    return FakeAoeClient()


@pytest.fixture
def created_client_policies() -> list[RequestPolicy]:
    return []


@pytest.fixture
def created_client_names(
    monkeypatch: pytest.MonkeyPatch,
    fake_client: FakeAoeClient,
    created_client_policies: list[RequestPolicy],
) -> list[ClientName]:
    names: list[ClientName] = []

    def create_fake_client(
        client_name: ClientName, _session: object, _version: str, policy: RequestPolicy
    ) -> AoeClient:
        names.append(client_name)
        created_client_policies.append(policy)
        return fake_client

    monkeypatch.setattr(client, "create_client", create_fake_client)
    return names
