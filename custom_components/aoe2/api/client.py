from typing import Protocol

from .models import Match, Profile


class AoeClient(Protocol):
    @property
    def attribution(self) -> str: ...

    @property
    def website_url(self) -> str: ...

    def profile_url(self, profile_id: int) -> str: ...

    async def get_profile(self, profile_id: int) -> Profile: ...

    async def get_recent_matches(self, profile_id: int, count: int = 5) -> list[Match]: ...
