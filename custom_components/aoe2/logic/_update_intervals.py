from dataclasses import dataclass
from datetime import timedelta

from custom_components.aoe2.models import PlayerData


@dataclass(frozen=True, slots=True)
class UpdateIntervals:
    usual: timedelta
    in_match: timedelta

    def for_data(self, data: PlayerData) -> timedelta:
        return self.in_match if data.is_in_current_match() else self.usual
