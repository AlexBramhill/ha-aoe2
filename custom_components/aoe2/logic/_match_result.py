from enum import StrEnum


class MatchResult(StrEnum):
    WIN = "win"
    LOSS = "loss"
    UNKNOWN = "unknown"


def get_match_result(is_player_winner: bool | None) -> MatchResult:
    match is_player_winner:
        case True:
            return MatchResult.WIN
        case False:
            return MatchResult.LOSS
        case None:
            return MatchResult.UNKNOWN
