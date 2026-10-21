from dataclasses import dataclass, field

from custom_components.aoe2.api import AoeClientError, Match, Profile
from tests.api.builders import MatchBuilder, ProfileBuilder


@dataclass
class FakeAoeClient:
    profile: Profile = field(default_factory=lambda: ProfileBuilder().build().expected)
    matches: list[Match] = field(default_factory=lambda: [MatchBuilder().build()])
    error: AoeClientError | None = None

    async def get_profile(self, profile_id: int) -> Profile:
        self._raise_error_if_set()
        return self.profile

    async def get_recent_matches(self, profile_id: int, count: int = 5) -> list[Match]:
        self._raise_error_if_set()
        return self.matches[:count]

    def _raise_error_if_set(self) -> None:
        if self.error is not None:
            raise self.error
