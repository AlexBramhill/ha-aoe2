from datetime import timedelta

from custom_components.aoe2.logic import PlayerData, get_unrecorded_matches
from tests.builders import TYPICAL_START, MatchBuilder, ProfileBuilder

PLAYER = ProfileBuilder().build().expected
OLDER_MATCH = MatchBuilder().with_match_id(1).build()
NEWER_MATCH = MatchBuilder().with_match_id(2).with_start(TYPICAL_START + timedelta(hours=1)).build()
CURRENT_MATCH = MatchBuilder().with_match_id(3).unfinished().build()


def test_unrecorded_matches_are_finished_and_oldest_first():
    # Given
    newest_first = PlayerData(profile=PLAYER, matches=(CURRENT_MATCH, NEWER_MATCH, OLDER_MATCH))

    # When
    unrecorded = get_unrecorded_matches(newest_first, recorded_ids=set())

    # Then
    assert unrecorded == [OLDER_MATCH, NEWER_MATCH]
