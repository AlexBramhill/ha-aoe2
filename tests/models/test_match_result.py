import pytest

from custom_components.aoe2.models import MatchResult


@pytest.mark.parametrize(
    ("is_winner", "expected"),
    [(True, MatchResult.WIN), (False, MatchResult.LOSS), (None, MatchResult.UNKNOWN)],
)
def test_match_result_comes_from_whether_the_player_won(
    is_winner: bool | None, expected: MatchResult
):
    # When
    result = MatchResult.from_is_winner(is_winner)

    # Then
    assert result is expected
