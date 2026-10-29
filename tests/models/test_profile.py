from custom_components.aoe2.models import Leaderboard
from tests.builders import build_rating


def test_win_rate_is_wins_over_games():
    # Given
    rating = build_rating(Leaderboard.RM_1V1, 1500, wins=3, losses=1)

    # Then
    assert rating.win_rate == 0.75


def test_win_rate_is_unknown_without_games():
    # Given
    rating = build_rating(Leaderboard.RM_1V1, 1500, wins=0, losses=0)

    # Then
    assert rating.win_rate is None
