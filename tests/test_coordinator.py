from datetime import timedelta

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_capture_events

from custom_components.aoe2.api import (
    AoeClientConnectionError,
    AoeClientError,
    AoeClientNotFoundError,
    AoeClientRateLimitError,
    AoeClientResponseError,
    Leaderboard,
)
from custom_components.aoe2.const import (
    CONF_CLIENT,
    CONF_PROFILE_ID,
    DOMAIN,
    EVENT_MATCH_FINISHED,
)
from custom_components.aoe2.coordinator import Aoe2Coordinator, Aoe2Data
from tests.api.builders import TYPICAL_START, MatchBuilder
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


async def test_refresh_provides_profile_and_matches(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # When
    await refresh(hass, coordinator)

    # Then
    expected = Aoe2Data(profile=fake_client.profile, matches=(EARLIER_MATCH.build(),))
    assert coordinator.data == expected


async def test_rate_limit_fails_update_with_retry_after(
    hass: HomeAssistant, coordinator: Aoe2Coordinator, fake_client: FakeAoeClient
):
    # Given
    fake_client.error = AoeClientRateLimitError("slow down", retry_after=30)

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
            "won": True,
            "rating_after_match": 1510,
            "rating_change": 10,
        }
    ]


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
