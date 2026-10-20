from collections.abc import Callable
from dataclasses import dataclass, replace
from types import ModuleType
from typing import Any, Self

from custom_components.aoe2.api import (
    AoeClientNotFoundError,
    ClientName,
    _aoe2companion,
    _worldsedge,
)
from tests.api.builders import ProfileBuilder
from tests.api.helpers import VIPER_PROFILE_ID, read_fixture

type Body = dict[str, Any]
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
    render_profile: Callable[[ProfileBuilder], Body]
    server_behaviour: ServerBehaviour = serve_unchanged

    def serving_profile(self, builder: ProfileBuilder) -> Self:
        path = self.profile_path(builder.profile_id)
        return replace(
            self, responses_by_path={**self.responses_by_path, path: self.render_profile(builder)}
        )

    async def get_json(self, _session: Any, url: str, params: Params | None = None) -> Body:
        path = url.removeprefix(f"{self.module.BASE_URL}/")
        if path not in self.responses_by_path:
            raise AoeClientNotFoundError(url)
        return self.server_behaviour(self.responses_by_path[path], params or {})


FAKE_APIS = [
    FakeApi(
        name="aoe2companion",
        module=_aoe2companion,
        responses_by_path={
            f"profiles/{VIPER_PROFILE_ID}": read_fixture("aoe2companion_profile.json"),
            "matches": read_fixture("aoe2companion_matches.json"),
        },
        profile_path=lambda profile_id: f"profiles/{profile_id}",
        render_profile=ProfileBuilder.aoe2companion_response,
        server_behaviour=limit_matches_to_per_page,
    ),
    FakeApi(
        name="worldsedge",
        module=_worldsedge,
        responses_by_path={
            "GetPersonalStat": read_fixture("worldsedge_stat.json"),
            "getRecentMatchHistory": read_fixture("worldsedge_matches.json"),
        },
        profile_path=lambda _profile_id: "GetPersonalStat",
        render_profile=ProfileBuilder.worldsedge_response,
    ),
]
