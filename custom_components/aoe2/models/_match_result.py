from enum import StrEnum


class MatchResult(StrEnum):
    WIN = "win"
    LOSS = "loss"
    UNKNOWN = "unknown"

    @classmethod
    def from_is_winner(cls, is_winner: bool | None) -> MatchResult:
        match is_winner:
            case True:
                return cls.WIN
            case False:
                return cls.LOSS
            case None:
                return cls.UNKNOWN
