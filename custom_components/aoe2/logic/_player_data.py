from dataclasses import dataclass

from ..api import Match, MatchPlayer, Profile


@dataclass(frozen=True, slots=True)
class PlayerData:
    profile: Profile
    matches: tuple[Match, ...]

    def finished_matches(self) -> tuple[Match, ...]:
        return tuple(match for match in self.matches if match.finished is not None)

    def last_finished_match(self) -> Match | None:
        return next(iter(self.finished_matches()), None)

    def current_match(self) -> Match | None:
        return next((match for match in self.matches if match.finished is None), None)

    def player_in(self, match: Match) -> MatchPlayer:
        return match.player_with_id(self.profile.profile_id)
