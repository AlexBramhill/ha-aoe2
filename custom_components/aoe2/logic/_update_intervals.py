from dataclasses import dataclass
from datetime import timedelta

from ._player_data import PlayerData


@dataclass(frozen=True, slots=True)
class UpdateIntervals:
    usual: timedelta
    in_match: timedelta

    def for_data(self, data: PlayerData) -> timedelta:
        return self.usual if data.current_match() is None else self.in_match
