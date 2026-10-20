"""AoE2 API clients. Nothing in this package imports Home Assistant."""

from collections.abc import Callable
from typing import Literal

import aiohttp

from .aoe2companion import Aoe2CompanionClient
from .client import AoeClient
from .errors import (
    AoeClientConnectionError,
    AoeClientError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
)
from .models import Leaderboard, Match, MatchPlayer, PlayerSummary, Profile, Rating
from .worldsedge import WorldsEdgeClient

ClientName = Literal["aoe2companion", "worldsedge"]

CLIENTS: dict[ClientName, Callable[[aiohttp.ClientSession], AoeClient]] = {
    "aoe2companion": Aoe2CompanionClient,
    "worldsedge": WorldsEdgeClient,
}


def create_client(client_name: ClientName, session: aiohttp.ClientSession) -> AoeClient:
    return CLIENTS[client_name](session)


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
    "PlayerSummary",
    "Profile",
    "Rating",
    "create_client",
]
