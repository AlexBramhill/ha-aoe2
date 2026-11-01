from datetime import timedelta

from custom_components.aoe2.logic import (
    MAX_RECORDED_MATCHES,
    RECENT_MATCH_COUNT,
    MatchLedger,
    get_newly_finished_matches,
)
from custom_components.aoe2.models import PlayerData
from tests.builders import TYPICAL_START, MatchBuilder, ProfileBuilder

PLAYER = ProfileBuilder().build().expected
OTHER_PROFILE_ID = PLAYER.profile_id + 1
OLDER_MATCH = MatchBuilder().with_match_id(1).build()
NEWER_MATCH = MatchBuilder().with_match_id(2).with_start(TYPICAL_START + timedelta(hours=1)).build()
CURRENT_MATCH = MatchBuilder().with_match_id(3).unfinished().build()

NEWEST_FIRST = PlayerData(
    profile=PLAYER, unsorted_matches=[CURRENT_MATCH, NEWER_MATCH, OLDER_MATCH]
)


def test_new_player_records_finished_matches_without_announcing_them():
    # When
    newly_finished, ledger = get_newly_finished_matches(NEWEST_FIRST, match_ledger=None)

    # Then
    assert ledger == MatchLedger(PLAYER.profile_id, (1, 2))
    assert newly_finished == []


def test_new_player_with_no_matches_still_gets_a_ledger():
    # Given
    data = PlayerData(profile=PLAYER, unsorted_matches=[])

    # When
    _, ledger = get_newly_finished_matches(data, match_ledger=None)

    # Then
    assert ledger == MatchLedger(PLAYER.profile_id)


def test_newly_finished_matches_are_announced_oldest_first():
    # Given
    saved = MatchLedger(PLAYER.profile_id)

    # When
    newly_finished, ledger = get_newly_finished_matches(NEWEST_FIRST, saved)

    # Then
    assert newly_finished == [OLDER_MATCH, NEWER_MATCH]
    assert ledger == MatchLedger(PLAYER.profile_id, (1, 2))


def test_recorded_matches_are_not_announced_again():
    # Given
    saved = MatchLedger(PLAYER.profile_id, (1, 2))

    # When
    newly_finished, ledger = get_newly_finished_matches(NEWEST_FIRST, saved)

    # Then
    assert newly_finished == []
    assert ledger == saved


def test_ledger_for_another_player_is_replaced_without_announcing():
    # Given
    saved = MatchLedger(OTHER_PROFILE_ID, (99,))

    # When
    newly_finished, ledger = get_newly_finished_matches(NEWEST_FIRST, saved)

    # Then
    assert ledger == MatchLedger(PLAYER.profile_id, (1, 2))
    assert newly_finished == []


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


def test_a_full_page_of_recent_matches_is_not_announced_again():
    # Given
    full_page = PlayerData(
        profile=PLAYER,
        unsorted_matches=[
            MatchBuilder()
            .with_match_id(match_id)
            .with_start(TYPICAL_START + timedelta(hours=match_id))
            .build()
            for match_id in range(RECENT_MATCH_COUNT)
        ],
    )
    _, ledger = get_newly_finished_matches(full_page, match_ledger=None)

    # When
    newly_finished, _ = get_newly_finished_matches(full_page, ledger)

    # Then
    assert newly_finished == []
