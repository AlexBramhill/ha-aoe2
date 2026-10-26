"""AoE2 API clients. Nothing in this package imports Home Assistant."""

from collections.abc import Callable
from typing import Literal

import aiohttp

from ._aoe2companion import Aoe2CompanionClient
from .client import AoeClient
from .errors import (
    AoeClientConnectionError,
    AoeClientError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
)
from .models import Leaderboard, Match, MatchPlayer, Profile, Rating

ClientName = Literal["aoe2companion"]

CLIENTS: dict[ClientName, Callable[[aiohttp.ClientSession, str], AoeClient]] = {
    "aoe2companion": Aoe2CompanionClient,
}


def create_client(
    client_name: ClientName, session: aiohttp.ClientSession, user_agent: str
) -> AoeClient:
    return CLIENTS[client_name](session, user_agent)


__all__ = [
    "CLIENTS",
    "AoeClient",
    "AoeClientConnectionError",
    "AoeClientError",
    "AoeClientNotFoundError",
    "AoeClientRateLimitError",
    "AoeClientResponseError",
    "ClientName",
    "Leaderboard",
    "Match",
    "MatchPlayer",
    "Profile",
    "Rating",
    "create_client",
]
