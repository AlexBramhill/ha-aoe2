"""AoE2 API clients. Nothing in this package imports Home Assistant."""

from collections.abc import Callable
from typing import Literal

import aiohttp

from custom_components.aoe2.api._aoe2companion import Aoe2CompanionClient
from custom_components.aoe2.api._http import (
    BACKGROUND_REQUESTS,
    INTERACTIVE_REQUESTS,
    RequestPolicy,
)
from custom_components.aoe2.api.client import AoeClient
from custom_components.aoe2.api.errors import (
    AoeClientConnectionError,
    AoeClientError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
    AoeClientRetryError,
)

ClientName = Literal["aoe2companion"]

CLIENTS: dict[ClientName, Callable[[aiohttp.ClientSession, str, RequestPolicy], AoeClient]] = {
    "aoe2companion": Aoe2CompanionClient,
}


def create_client(
    client_name: ClientName,
    session: aiohttp.ClientSession,
    version: str,
    policy: RequestPolicy = BACKGROUND_REQUESTS,
) -> AoeClient:
    return CLIENTS[client_name](session, version, policy)


__all__ = [
    "BACKGROUND_REQUESTS",
    "CLIENTS",
    "INTERACTIVE_REQUESTS",
    "AoeClient",
    "AoeClientConnectionError",
    "AoeClientError",
    "AoeClientNotFoundError",
    "AoeClientRateLimitError",
    "AoeClientResponseError",
    "AoeClientRetryError",
    "ClientName",
    "RequestPolicy",
    "create_client",
]
