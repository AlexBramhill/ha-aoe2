from dataclasses import dataclass

from custom_components.aoe2.models._match import Match, MatchPlayer
from custom_components.aoe2.models._profile import Profile


@dataclass(frozen=True, slots=True)
class PlayerData:
    profile: Profile
    matches: tuple[Match, ...]

    def finished_matches(self) -> tuple[Match, ...]:
        return tuple(match for match in self.matches if match.is_finished)

    def last_finished_match(self) -> Match | None:
        return next(iter(self.finished_matches()), None)

    def current_match(self) -> Match | None:
        return next((match for match in self.matches if not match.is_finished), None)

    def is_in_current_match(self) -> bool:
        return self.current_match() is not None

    def player_in(self, match: Match) -> MatchPlayer:
        return match.get_player_with_id(self.profile.profile_id)

    def recent_win_rate(self) -> float | None:
        results = [self.player_in(match).is_winner for match in self.finished_matches()]
        known_results = [is_winner for is_winner in results if is_winner is not None]
        return known_results.count(True) / len(known_results) if known_results else None

    def recent_rating_change(self) -> int | None:
        changes = [self.player_in(match).rating_change for match in self.finished_matches()]
        known_changes = [change for change in changes if change is not None]
        return sum(known_changes) if known_changes else None
