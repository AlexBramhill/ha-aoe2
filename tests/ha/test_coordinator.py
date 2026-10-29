from datetime import timedelta
from typing import Any

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_capture_events

from custom_components.aoe2.api import (
    AoeClientConnectionError,
    AoeClientError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
)
from custom_components.aoe2.const import (
    CONF_CLIENT,
    CONF_IN_MATCH_UPDATE_MINUTES,
    CONF_PROFILE_ID,
    CONF_UPDATE_MINUTES,
    DOMAIN,
    EVENT_MATCH_FINISHED,
    MIN_IN_MATCH_UPDATE_MINUTES,
    MIN_UPDATE_MINUTES,
)
from custom_components.aoe2.ha.coordinator import Aoe2Coordinator, get_update_intervals
from custom_components.aoe2.logic import MatchFinishedEvent
from custom_components.aoe2.models import Leaderboard, PlayerData
from tests.builders import TYPICAL_START, MatchBuilder
from tests.fake_client import FakeAoeClient

PROFILE_ID = 1
EARLIER_MATCH = MatchBuilder().with_match_id(1)
NEWER_MATCH = MatchBuilder().with_match_id(2).with_start(TYPICAL_START + timedelta(hours=1))


@pytest.fixture
def fake_client() -> FakeAoeClient:
    return FakeAoeClient(matches=[EARLIER_MATCH.build()])


@pytest.fixture
def coordinator(hass: HomeAssistant, fake_client: FakeAoeClient) -> Aoe2Coordinator:
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_CLIENT: "aoe2companion", CONF_PROFILE_ID: PROFILE_ID}
    )
    entry.add_to_hass(hass)
    return Aoe2Coordinator(hass, entry, fake_client)


async def refresh(hass: HomeAssistant, coordinator: Aoe2Coordinator) -> None:
    await coordinator.async_refresh()
    await hass.async_block_till_done()


async def start(hass: HomeAssistant, coordinator: Aoe2Coordinator) -> None:
    coordinator.config_entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)
    await coordinator.async_config_entry_first_refresh()
    await hass.async_block_till_done()


async def test_refresh_provides_profile_and_matches(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # When
    await refresh(hass, coordinator)

    # Then
    expected = PlayerData(profile=fake_client.profile, matches=(EARLIER_MATCH.build(),))
    assert coordinator.data == expected


@pytest.mark.parametrize(
    "error",
    [
        AoeClientRateLimitError("slow down", retry_after=30),
        AoeClientConnectionError("unavailable", retry_after=30),
    ],
    ids=["rate-limit", "connection"],
)
async def test_retry_after_is_passed_to_failed_update(
    hass: HomeAssistant,
    coordinator: Aoe2Coordinator,
    fake_client: FakeAoeClient,
    error: AoeClientError,
):
    # Given
    fake_client.error = error

    # When
    await refresh(hass, coordinator)

    # Then
    assert not coordinator.last_update_success
    assert isinstance(coordinator.last_exception, UpdateFailed)
    assert coordinator.last_exception.retry_after == 30


@pytest.mark.parametrize(
    "error",
    [
        AoeClientConnectionError("unreachable"),
        AoeClientResponseError("unexpected"),
        AoeClientNotFoundError("gone"),
    ],
    ids=["connection", "response", "not-found"],
)
async def test_client_error_fails_update(
    hass: HomeAssistant,
    coordinator: Aoe2Coordinator,
    fake_client: FakeAoeClient,
    error: AoeClientError,
):
    # Given
    fake_client.error = error

    # When
    await refresh(hass, coordinator)

    # Then
    assert not coordinator.last_update_success
    assert isinstance(coordinator.last_exception, UpdateFailed)
    assert coordinator.last_exception.retry_after is None


async def test_first_refresh_does_not_announce_matches(
    hass: HomeAssistant, coordinator: Aoe2Coordinator
):
    # Given
    events = async_capture_events(hass, EVENT_MATCH_FINISHED)

    # When
    await refresh(hass, coordinator)

    # Then
    assert events == []


async def test_newly_finished_match_is_announced(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # Given
    await refresh(hass, coordinator)
    events = async_capture_events(hass, EVENT_MATCH_FINISHED)
    fake_client.matches = [NEWER_MATCH.build(), EARLIER_MATCH.build()]

    # When
    await refresh(hass, coordinator)

    # Then
    assert [event.data for event in events] == [
        {
            "profile_id": PROFILE_ID,
            "match_id": 2,
            "leaderboard": Leaderboard.RM_1V1,
            "map_name": "Arabia",
            "is_winner": True,
            "rating_after_match": 1510,
            "rating_change": 10,
        }
    ]


async def test_match_finished_listeners_hear_newly_finished_match(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # Given
    await refresh(hass, coordinator)
    heard: list[MatchFinishedEvent] = []
    coordinator.async_add_match_finished_listener(heard.append)
    fake_client.matches = [NEWER_MATCH.build(), EARLIER_MATCH.build()]

    # When
    await refresh(hass, coordinator)

    # Then
    assert [event.match_id for event in heard] == [2]


async def test_removed_match_finished_listener_hears_nothing(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # Given
    await refresh(hass, coordinator)
    heard: list[MatchFinishedEvent] = []
    remove_listener = coordinator.async_add_match_finished_listener(heard.append)
    remove_listener()
    fake_client.matches = [NEWER_MATCH.build(), EARLIER_MATCH.build()]

    # When
    await refresh(hass, coordinator)

    # Then
    assert heard == []


async def test_unfinished_match_is_not_announced(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # Given
    await refresh(hass, coordinator)
    events = async_capture_events(hass, EVENT_MATCH_FINISHED)
    fake_client.matches = [NEWER_MATCH.unfinished().build(), EARLIER_MATCH.build()]

    # When
    await refresh(hass, coordinator)

    # Then
    assert events == []


async def test_match_is_announced_once_it_finishes(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # Given
    await refresh(hass, coordinator)
    fake_client.matches = [NEWER_MATCH.unfinished().build(), EARLIER_MATCH.build()]
    await refresh(hass, coordinator)
    events = async_capture_events(hass, EVENT_MATCH_FINISHED)
    fake_client.matches = [NEWER_MATCH.build(), EARLIER_MATCH.build()]

    # When
    await refresh(hass, coordinator)

    # Then
    assert [event.data["match_id"] for event in events] == [2]


async def test_announced_match_is_not_announced_again(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # Given
    await refresh(hass, coordinator)
    fake_client.matches = [NEWER_MATCH.build(), EARLIER_MATCH.build()]
    await refresh(hass, coordinator)
    events = async_capture_events(hass, EVENT_MATCH_FINISHED)

    # When
    await refresh(hass, coordinator)

    # Then
    assert events == []


async def test_empty_response_does_not_cause_matches_to_be_announced_again(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # Given
    await refresh(hass, coordinator)
    fake_client.matches = [NEWER_MATCH.build(), EARLIER_MATCH.build()]
    await refresh(hass, coordinator)
    fake_client.matches = []
    await refresh(hass, coordinator)
    events = async_capture_events(hass, EVENT_MATCH_FINISHED)
    fake_client.matches = [NEWER_MATCH.build(), EARLIER_MATCH.build()]

    # When
    await refresh(hass, coordinator)

    # Then
    assert events == []


async def test_first_refresh_records_existing_matches(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, hass_storage: dict[str, Any]
):
    # When
    await refresh(hass, coordinator)

    # Then
    stored = hass_storage[storage_key(coordinator)]["data"]
    assert stored["match_ids"] == [1]


async def test_restart_does_not_announce_matches_again(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # Given
    await refresh(hass, coordinator)
    fake_client.matches = [NEWER_MATCH.build(), EARLIER_MATCH.build()]
    await refresh(hass, coordinator)
    restarted = Aoe2Coordinator(hass, coordinator.config_entry, fake_client)
    events = async_capture_events(hass, EVENT_MATCH_FINISHED)

    # When
    await start(hass, restarted)

    # Then
    assert events == []


async def test_restart_announces_match_that_finished_while_stopped(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # Given
    await refresh(hass, coordinator)
    fake_client.matches = [NEWER_MATCH.build(), EARLIER_MATCH.build()]
    restarted = Aoe2Coordinator(hass, coordinator.config_entry, fake_client)
    events = async_capture_events(hass, EVENT_MATCH_FINISHED)

    # When
    await start(hass, restarted)

    # Then
    assert [event.data["match_id"] for event in events] == [2]


def storage_key(coordinator: Aoe2Coordinator) -> str:
    return f"{DOMAIN}.{coordinator.config_entry.entry_id}.recorded_matches"


async def test_polls_more_often_during_a_match(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # Given
    fake_client.matches = [NEWER_MATCH.unfinished().build(), EARLIER_MATCH.build()]

    # When
    await refresh(hass, coordinator)

    # Then
    assert coordinator.update_interval == timedelta(minutes=MIN_IN_MATCH_UPDATE_MINUTES)


async def test_returns_to_normal_polling_after_the_match(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # Given
    fake_client.matches = [NEWER_MATCH.unfinished().build(), EARLIER_MATCH.build()]
    await refresh(hass, coordinator)
    fake_client.matches = [NEWER_MATCH.build(), EARLIER_MATCH.build()]

    # When
    await refresh(hass, coordinator)

    # Then
    assert coordinator.update_interval == timedelta(minutes=MIN_UPDATE_MINUTES)


def test_update_intervals_default_to_the_minimums():
    # When
    intervals = get_update_intervals({})

    # Then
    assert intervals.usual == timedelta(minutes=MIN_UPDATE_MINUTES)
    assert intervals.in_match == timedelta(minutes=MIN_IN_MATCH_UPDATE_MINUTES)


def test_update_intervals_come_from_options():
    # When
    intervals = get_update_intervals({CONF_UPDATE_MINUTES: 30, CONF_IN_MATCH_UPDATE_MINUTES: 5})

    # Then
    assert intervals.usual == timedelta(minutes=30)
    assert intervals.in_match == timedelta(minutes=5)
