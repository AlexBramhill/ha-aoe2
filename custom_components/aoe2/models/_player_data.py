from dataclasses import InitVar, dataclass, field
from datetime import datetime

from custom_components.aoe2.models._match import Match, MatchPlayer
from custom_components.aoe2.models._match_result import MatchResult
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

    def get_finished_matches(self) -> tuple[Match, ...]:
        return tuple(match for match in self.matches if match.is_finished)

    def get_last_finished_match(self) -> Match | None:
        return next(iter(self.get_finished_matches()), None)

    def get_current_match(self) -> Match | None:
        return next((match for match in self.matches if not match.is_finished), None)

    def is_in_current_match(self) -> bool:
        return self.get_current_match() is not None

    def get_own_player_in(self, match: Match) -> MatchPlayer:
        return match.get_player_with_id(self.profile.profile_id)

    def get_last_match_result(self) -> MatchResult:
        player = self._get_own_player_in_last_match()
        return MatchResult.UNKNOWN if player is None else player.result

    def get_last_match_rating_change(self) -> int | None:
        player = self._get_own_player_in_last_match()
        return None if player is None else player.rating_change

    def get_last_match_civ(self) -> str | None:
        player = self._get_own_player_in_last_match()
        return None if player is None else player.civ

    def get_last_match_map(self) -> str | None:
        match = self.get_last_finished_match()
        return None if match is None else match.map_name

    def get_last_match_finished_at(self) -> datetime | None:
        match = self.get_last_finished_match()
        return None if match is None else match.finished

    def get_recent_win_rate(self) -> float | None:
        results = [self.get_own_player_in(match).result for match in self.get_finished_matches()]
        known_results = [result for result in results if result is not MatchResult.UNKNOWN]
        return known_results.count(MatchResult.WIN) / len(known_results) if known_results else None

    def get_recent_rating_change(self) -> int | None:
        changes = [
            self.get_own_player_in(match).rating_change for match in self.get_finished_matches()
        ]
        known_changes = [change for change in changes if change is not None]
        return sum(known_changes) if known_changes else None

    def _check_player_is_in_every_match(self, matches: list[Match]) -> None:
        profile_id = self.profile.profile_id
        missing = [match.match_id for match in matches if not match.has_player_with_id(profile_id)]
        if missing:
            raise ValueError(f"Profile {profile_id} did not play in matches {missing}")

    def _get_own_player_in_last_match(self) -> MatchPlayer | None:
        match = self.get_last_finished_match()
        return None if match is None else self.get_own_player_in(match)
