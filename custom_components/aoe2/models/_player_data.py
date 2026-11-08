from dataclasses import InitVar, dataclass, field

from custom_components.aoe2.models._match import Match, MatchPlayer
from custom_components.aoe2.models._match_result import MatchResult
from custom_components.aoe2.models._profile import Profile


@dataclass(frozen=True, slots=True)
class PlayerData:
    profile: Profile
    unsorted_matches: InitVar[list[Match]]
    matches_newest_first: tuple[Match, ...] = field(init=False)

    def __post_init__(self, unsorted_matches: list[Match]) -> None:
        self._check_player_is_in_every_match(unsorted_matches)
        newest_first = sorted(unsorted_matches, key=lambda match: match.started, reverse=True)
        object.__setattr__(self, "matches_newest_first", tuple(newest_first))

    def get_finished_matches_newest_first(self) -> tuple[Match, ...]:
        return tuple(match for match in self.matches_newest_first if match.is_finished)

    def get_last_finished_match(self) -> Match | None:
        return next((match for match in self.matches_newest_first if match.is_finished), None)

    def get_current_match(self) -> Match | None:
        return next((match for match in self.matches_newest_first if not match.is_finished), None)

    def is_in_current_match(self) -> bool:
        return self.get_current_match() is not None

    def get_own_player_in(self, match: Match) -> MatchPlayer:
        return match.get_player_with_id(self.profile.profile_id)

    def get_recent_win_rate(self) -> float | None:
        known_results = [
            player.result
            for player in self._get_own_player_per_finished_match()
            if player.result is not MatchResult.UNKNOWN
        ]
        if not known_results:
            return None
        return known_results.count(MatchResult.WIN) / len(known_results)

    def get_recent_rating_change(self) -> int | None:
        known_changes = [
            player.rating_change
            for player in self._get_own_player_per_finished_match()
            if player.rating_change is not None
        ]
        if not known_changes:
            return None
        return sum(known_changes)

    def _check_player_is_in_every_match(self, matches: list[Match]) -> None:
        profile_id = self.profile.profile_id
        missing = [match.match_id for match in matches if not match.has_player_with_id(profile_id)]
        if missing:
            raise ValueError(f"Profile {profile_id} did not play in matches {missing}")

    def _get_own_player_per_finished_match(self) -> list[MatchPlayer]:
        return [self.get_own_player_in(match) for match in self.get_finished_matches_newest_first()]
