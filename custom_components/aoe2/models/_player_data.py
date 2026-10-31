from dataclasses import InitVar, dataclass, field
from datetime import datetime

from custom_components.aoe2.models import MatchResult
from custom_components.aoe2.models._match import Match, MatchPlayer
from custom_components.aoe2.models._profile import Profile


@dataclass(frozen=True, slots=True)
class PlayerData:
    profile: Profile
    unsorted_matches: InitVar[list[Match]]
    matches: tuple[Match, ...] = field(init=False)

    def __post_init__(self, unsorted_matches: list[Match]) -> None:
        self._check_player_is_in_every_match(unsorted_matches)
        newest_first = sorted(unsorted_matches, key=lambda match: match.started, reverse=True)
        object.__setattr__(self, "matches", tuple(newest_first))

    def finished_matches(self) -> tuple[Match, ...]:
        return tuple(match for match in self.matches if match.is_finished)

    def last_finished_match(self) -> Match | None:
        return next(iter(self.finished_matches()), None)

    def current_match(self) -> Match | None:
        return next((match for match in self.matches if not match.is_finished), None)

    def is_in_current_match(self) -> bool:
        return self.current_match() is not None

    def own_player_in(self, match: Match) -> MatchPlayer:
        return match.get_player_with_id(self.profile.profile_id)

    def last_match_result(self) -> MatchResult | None:
        player = self._own_player_in_last_match()
        return None if player is None else player.result

    def last_match_rating_change(self) -> int | None:
        player = self._own_player_in_last_match()
        return None if player is None else player.rating_change

    def last_match_civ(self) -> str | None:
        player = self._own_player_in_last_match()
        return None if player is None else player.civ

    def last_match_map(self) -> str | None:
        match = self.last_finished_match()
        return None if match is None else match.map_name

    def last_match_finished_at(self) -> datetime | None:
        match = self.last_finished_match()
        return None if match is None else match.finished

    def recent_win_rate(self) -> float | None:
        results = [self.own_player_in(match).result for match in self.finished_matches()]
        return results.count(MatchResult.WIN) / len(results) if results else None

    def recent_rating_change(self) -> int | None:
        changes = [self.own_player_in(match).rating_change for match in self.finished_matches()]
        known_changes = [change for change in changes if change is not None]
        return sum(known_changes) if known_changes else None

    def _check_player_is_in_every_match(self, matches: list[Match]) -> None:
        profile_id = self.profile.profile_id
        missing = [match.match_id for match in matches if not match.has_player_with_id(profile_id)]
        if missing:
            raise ValueError(f"Profile {profile_id} did not play in matches {missing}")

    def _own_player_in_last_match(self) -> MatchPlayer | None:
        match = self.last_finished_match()
        return None if match is None else self.own_player_in(match)
