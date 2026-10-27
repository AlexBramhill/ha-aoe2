import pytest

from custom_components.aoe2.api import AoeClient, ClientName
from tests.fake_client import FakeAoeClient

MODULES_CREATING_CLIENTS = ["custom_components.aoe2", "custom_components.aoe2.config_flow"]


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    return


@pytest.fixture
def fake_client() -> FakeAoeClient:
    return FakeAoeClient()


@pytest.fixture
def created_client_names(
    monkeypatch: pytest.MonkeyPatch, fake_client: FakeAoeClient
) -> list[ClientName]:
    names: list[ClientName] = []

    def create_fake_client(
        client_name: ClientName, _session: object, _user_agent: str
    ) -> AoeClient:
        names.append(client_name)
        return fake_client

    for module in MODULES_CREATING_CLIENTS:
        monkeypatch.setattr(f"{module}.create_client", create_fake_client)
    return names
