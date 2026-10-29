"""Data the integration works with, whichever source it came from.

Nothing in this package imports Home Assistant.
"""

from custom_components.aoe2.models._leaderboard import Leaderboard
from custom_components.aoe2.models._match import Match, MatchPlayer
from custom_components.aoe2.models._profile import Profile, Rating

__all__ = ["Leaderboard", "Match", "MatchPlayer", "Profile", "Rating"]
