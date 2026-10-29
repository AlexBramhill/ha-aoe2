from enum import StrEnum
from typing import Self


class MatchResult(StrEnum):
    WIN = "win"
    LOSS = "loss"
    UNKNOWN = "unknown"

    @classmethod
    def from_is_winner(cls, is_winner: bool | None) -> Self:
        match is_winner:
            case True:
                return cls.WIN
            case False:
                return cls.LOSS
            case None:
                return cls.UNKNOWN
