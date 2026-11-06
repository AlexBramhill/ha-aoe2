import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from types import ModuleType
from typing import Self

from pydantic import BaseModel

from custom_components.aoe2.api import (
    AoeClientNotFoundError,
    ClientName,
    RequestPolicy,
    _aoe2companion,
)
from tests.api.api_json import Body
from tests.api.helpers import RecordedPlayer
from tests.builders import BuiltMatchHistory, BuiltProfile
from tests.json_values import get_list_at

type Params = Mapping[str, str | int]
type ServerBehaviour = Callable[[Body, Params], Body]


def serve_unchanged(body: Body, _params: Params) -> Body:
    return body


def get_per_page(params: Params) -> int:
    per_page = params["per_page"]
    assert isinstance(per_page, int)
    return per_page


def limit_matches_to_per_page(body: Body, params: Params) -> Body:
    if "per_page" not in params or "matches" not in body:
        return body
    return {**body, "matches": get_list_at(body, "matches")[: get_per_page(params)]}


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

    async def get_response[Response: BaseModel](
        self,
        _session: object,
        url: str,
        response_type: type[Response],
        params: Params | None = None,
        *,
        version: str,
        policy: RequestPolicy,
    ) -> Response:
        del version, policy
        path = url.removeprefix(f"{_aoe2companion.BASE_URL}/")
        if path not in self.responses_by_path:
            raise AoeClientNotFoundError(url)
        body = self.server_behaviour(self.responses_by_path[path], params or {})
        return response_type.model_validate_json(json.dumps(body))


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
