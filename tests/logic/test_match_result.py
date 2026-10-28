import pytest

from custom_components.aoe2.logic import MatchResult, get_match_result


@pytest.mark.parametrize(
    ("won", "expected"),
    [(True, MatchResult.WIN), (False, MatchResult.LOSS), (None, MatchResult.UNKNOWN)],
)
def test_match_result_comes_from_whether_the_player_won(won: bool | None, expected: MatchResult):
    # When
    result = get_match_result(won)

    # Then
    assert result is expected
