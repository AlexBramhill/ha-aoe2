"""AoE2 API clients. Nothing in this package imports Home Assistant."""

from collections.abc import Callable
from typing import Literal

import aiohttp

from ._aoe2companion import Aoe2CompanionClient
from ._http import BACKGROUND_REQUESTS, INTERACTIVE_REQUESTS, RequestPolicy
from .client import AoeClient
from .errors import (
    AoeClientConnectionError,
    AoeClientError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
    AoeClientRetryError,
)
from .models import Leaderboard, Match, MatchPlayer, Profile, Rating

ClientName = Literal["aoe2companion"]

CLIENTS: dict[ClientName, Callable[[aiohttp.ClientSession, str, RequestPolicy], AoeClient]] = {
    "aoe2companion": Aoe2CompanionClient,
}


def create_client(
    client_name: ClientName,
    session: aiohttp.ClientSession,
    user_agent: str,
    policy: RequestPolicy = BACKGROUND_REQUESTS,
) -> AoeClient:
    return CLIENTS[client_name](session, user_agent, policy)


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
    "Leaderboard",
    "Match",
    "MatchPlayer",
    "Profile",
    "Rating",
    "RequestPolicy",
    "create_client",
]
