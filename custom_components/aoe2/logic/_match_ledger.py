from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import Self

from custom_components.aoe2.logic._player_data import PlayerData
from custom_components.aoe2.models import Match

MAX_RECORDED_MATCHES = 1000


@dataclass(frozen=True, slots=True)
class MatchLedger:
    profile_id: int
    match_ids: tuple[int, ...] = ()

    def __contains__(self, match_id: int) -> bool:
        return match_id in self.match_ids

    def record(self, match_ids: Iterable[int]) -> Self:
        recorded = list(self.match_ids)
        for match_id in match_ids:
            if match_id not in recorded:
                recorded.append(match_id)
        return replace(self, match_ids=tuple(recorded[-MAX_RECORDED_MATCHES:]))


@dataclass(frozen=True, slots=True)
class MatchCheck:
    ledger: MatchLedger
    to_announce: list[Match]


def get_new_matches(data: PlayerData, match_ledger: MatchLedger | None) -> MatchCheck:
    finished_oldest_first = list(reversed(data.finished_matches()))

    if match_ledger is None or match_ledger.profile_id != data.profile.profile_id:
        new_ledger = MatchLedger(data.profile.profile_id).record(
            match.match_id for match in finished_oldest_first
        )
        return MatchCheck(ledger=new_ledger, to_announce=[])

    unrecorded = [match for match in finished_oldest_first if match.match_id not in match_ledger]
    return MatchCheck(
        ledger=match_ledger.record(match.match_id for match in unrecorded),
        to_announce=unrecorded,
    )
