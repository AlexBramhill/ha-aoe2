from typing import Protocol

from .models import Match, PlayerSummary, Profile


class AoeClient(Protocol):
    async def search_players(self, name: str) -> list[PlayerSummary]: ...

    async def get_profile(self, profile_id: int) -> Profile: ...

    async def get_recent_matches(self, profile_id: int, count: int = 5) -> list[Match]: ...
