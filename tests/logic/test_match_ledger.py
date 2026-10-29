from datetime import timedelta

from custom_components.aoe2.logic import (
    MAX_RECORDED_MATCHES,
    MatchLedger,
    PlayerData,
    get_new_matches,
)
from tests.builders import TYPICAL_START, MatchBuilder, ProfileBuilder

PLAYER = ProfileBuilder().build().expected
OTHER_PROFILE_ID = PLAYER.profile_id + 1
OLDER_MATCH = MatchBuilder().with_match_id(1).build()
NEWER_MATCH = MatchBuilder().with_match_id(2).with_start(TYPICAL_START + timedelta(hours=1)).build()
CURRENT_MATCH = MatchBuilder().with_match_id(3).unfinished().build()

NEWEST_FIRST = PlayerData(profile=PLAYER, matches=(CURRENT_MATCH, NEWER_MATCH, OLDER_MATCH))


def test_new_player_records_finished_matches_without_announcing_them():
    # When
    check = get_new_matches(NEWEST_FIRST, match_ledger=None)

    # Then
    assert check.ledger == MatchLedger(PLAYER.profile_id, (1, 2))
    assert check.to_announce == []


def test_new_player_with_no_matches_still_gets_a_ledger():
    # Given
    data = PlayerData(profile=PLAYER, matches=())

    # When
    check = get_new_matches(data, match_ledger=None)

    # Then
    assert check.ledger == MatchLedger(PLAYER.profile_id)


def test_unrecorded_matches_are_announced_oldest_first():
    # Given
    saved = MatchLedger(PLAYER.profile_id)

    # When
    check = get_new_matches(NEWEST_FIRST, saved)

    # Then
    assert check.to_announce == [OLDER_MATCH, NEWER_MATCH]
    assert check.ledger == MatchLedger(PLAYER.profile_id, (1, 2))


def test_recorded_matches_are_not_announced_again():
    # Given
    saved = MatchLedger(PLAYER.profile_id, (1, 2))

    # When
    check = get_new_matches(NEWEST_FIRST, saved)

    # Then
    assert check.to_announce == []
    assert check.ledger == saved


def test_ledger_for_another_player_is_replaced_without_announcing():
    # Given
    saved = MatchLedger(OTHER_PROFILE_ID, (99,))

    # When
    check = get_new_matches(NEWEST_FIRST, saved)

    # Then
    assert check.ledger == MatchLedger(PLAYER.profile_id, (1, 2))
    assert check.to_announce == []


def test_recording_an_id_twice_keeps_one_copy():
    # Given
    ledger = MatchLedger(PLAYER.profile_id, (1,))

    # When
    recorded = ledger.record([1, 2, 2])

    # Then
    assert recorded.match_ids == (1, 2)


def test_recording_keeps_only_the_most_recent_ids():
    # Given
    oldest_kept = 6

    # When
    recorded = MatchLedger(PLAYER.profile_id).record(range(1, MAX_RECORDED_MATCHES + oldest_kept))

    # Then
    assert len(recorded.match_ids) == MAX_RECORDED_MATCHES
    assert oldest_kept - 1 not in recorded
    assert oldest_kept in recorded
