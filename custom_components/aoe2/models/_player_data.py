from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime

from custom_components.aoe2.models import MatchResult
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

    def last_match_result(self) -> MatchResult | None:
        return self._player_stats_for_last_match(lambda player: player.result)

    def last_match_rating_change(self) -> int | None:
        return self._player_stats_for_last_match(lambda player: player.rating_change)

    def last_match_civ(self) -> str | None:
        return self._player_stats_for_last_match(lambda player: player.civ)

    def last_match_map(self) -> str | None:
        return self._match_stats_for_last_match(lambda match: match.map_name)

    def last_played(self) -> datetime | None:
        return self._match_stats_for_last_match(lambda match: match.finished)

    def recent_win_rate(self) -> float | None:
        results = [self._player_data_for_match(match).result for match in self.finished_matches()]
        return results.count(MatchResult.WIN) / len(results) if results else None

    def recent_rating_change(self) -> int | None:
        changes = [
            self._player_data_for_match(match).rating_change for match in self.finished_matches()
        ]
        known_changes = [change for change in changes if change is not None]
        return sum(known_changes) if known_changes else None


    def _match_stats_for_last_match[Value](
        self, callback: Callable[[Match], Value]
    ) -> Value | None:
        last_match = self.last_finished_match()
        return None if last_match is None else callback(last_match)

    def _player_data_for_match(self, match: Match) -> MatchPlayer:
        return match.get_player_with_id(self.profile.profile_id)

    def _player_data_for_last_match(
            self,
        ) -> MatchPlayer | None:
            return self._match_stats_for_last_match(
                lambda match: self._player_data_for_match(match)
            )

    def _player_stats_for_last_match[Value](
        self, callback: Callable[[MatchPlayer], Value]
    ) -> Value | None:
        player_data_for_last_match = self._player_data_for_last_match()
        return None if player_data_for_last_match is None else callback(player_data_for_last_match)
