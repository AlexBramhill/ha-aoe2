from collections.abc import Callable
from dataclasses import dataclass, replace
from types import ModuleType
from typing import Any, Self

from custom_components.aoe2.api import (
    AoeClientNotFoundError,
    ClientName,
    RequestPolicy,
    _aoe2companion,
)
from tests.api.api_json import Body
from tests.api.helpers import RecordedPlayer
from tests.builders import BuiltMatchHistory, BuiltProfile

type Params = dict[str, Any]
type ServerBehaviour = Callable[[Body, Params], Body]


def serve_unchanged(body: Body, _params: Params) -> Body:
    return body


def limit_matches_to_per_page(body: Body, params: Params) -> Body:
    if "per_page" not in params or "matches" not in body:
        return body
    return {**body, "matches": body["matches"][: params["per_page"]]}


@dataclass(frozen=True)
class FakeApi:
    name: ClientName
    module: ModuleType
    responses_by_path: dict[str, Body]
    profile_path: Callable[[int], str]
    profile_response: Callable[[BuiltProfile], Body]
    matches_path: str
    matches_response: Callable[[BuiltMatchHistory], Body]
    server_behaviour: ServerBehaviour = serve_unchanged

    def serving_profile(self, built: BuiltProfile) -> Self:
        path = self.profile_path(built.expected.profile_id)
        return self._serving(path, self.profile_response(built))

    def serving_matches(self, history: BuiltMatchHistory) -> Self:
        return self._serving(self.matches_path, self.matches_response(history))

    def _serving(self, path: str, body: Body) -> Self:
        return replace(self, responses_by_path={**self.responses_by_path, path: body})

    async def get_json(
        self,
        _session: Any,
        url: str,
        params: Params | None = None,
        *,
        user_agent: str,
        policy: RequestPolicy,
    ) -> Body:
        path = url.removeprefix(f"{self.module.BASE_URL}/")
        if path not in self.responses_by_path:
            raise AoeClientNotFoundError(url)
        return self.server_behaviour(self.responses_by_path[path], params or {})


def aoe2companion_fake(player: RecordedPlayer) -> FakeApi:
    return FakeApi(
        name="aoe2companion",
        module=_aoe2companion,
        responses_by_path={
            f"profiles/{player.profile_id}": player.read_fixture("aoe2companion_profile.json"),
            "matches": player.read_fixture("aoe2companion_matches.json"),
        },
        profile_path=lambda profile_id: f"profiles/{profile_id}",
        profile_response=lambda built: built.aoe2companion_response,
        matches_path="matches",
        matches_response=lambda history: history.aoe2companion_response,
        server_behaviour=limit_matches_to_per_page,
    )


FAKE_API_FOR_CLIENT: dict[ClientName, Callable[[RecordedPlayer], FakeApi]] = {
    "aoe2companion": aoe2companion_fake,
}
