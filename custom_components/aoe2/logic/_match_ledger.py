from collections.abc import Iterable
from dataclasses import dataclass, replace
from typing import Self

from custom_components.aoe2.api import Match
from custom_components.aoe2.logic._player_data import PlayerData

MAX_RECORDED_MATCHES = 1000


@dataclass(frozen=True, slots=True)
class MatchLedger:
    """Finished matches already handled for a player, oldest first."""

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
class NewMatches:
    ledger: MatchLedger
    to_announce: list[Match]
    needs_saving: bool


def get_new_matches(data: PlayerData, saved: MatchLedger | None) -> NewMatches:
    finished_oldest_first = list(reversed(data.finished_matches()))
    if saved is None or saved.profile_id != data.profile.profile_id:
        # A newly added player: their existing matches are recorded, not announced.
        ledger = MatchLedger(data.profile.profile_id).record(
            match.match_id for match in finished_oldest_first
        )
        return NewMatches(ledger=ledger, to_announce=[], needs_saving=True)

    unrecorded = [match for match in finished_oldest_first if match.match_id not in saved]
    return NewMatches(
        ledger=saved.record(match.match_id for match in unrecorded),
        to_announce=unrecorded,
        needs_saving=bool(unrecorded),
    )
