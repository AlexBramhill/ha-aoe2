import asyncio
from collections.abc import Mapping
from datetime import timedelta
from typing import Any, TypedDict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import TimestampDataUpdateCoordinator, UpdateFailed

from custom_components.aoe2.api import AoeClient, AoeClientError, AoeClientRetryError, Leaderboard, Match
from custom_components.aoe2.const import (
    CONF_IN_MATCH_UPDATE_MINUTES,
    CONF_PROFILE_ID,
    CONF_UPDATE_MINUTES,
    DOMAIN,
    EVENT_MATCH_FINISHED,
    LOGGER,
    MIN_IN_MATCH_UPDATE_MINUTES,
    MIN_UPDATE_MINUTES,
)
from custom_components.aoe2.logic import (
    MatchFinishedEvent,
    PlayerData,
    UpdateIntervals,
    get_match_finished_event,
    get_matches_to_announce,
    get_unrecorded_matches,
)
from .recorded_matches import RecordedMatches

RECENT_MATCH_COUNT = 5

type Aoe2ConfigEntry = ConfigEntry[Aoe2Coordinator]


class MatchFinishedEventData(TypedDict):
    """Flat, because automations read these fields as event entity attributes."""

    profile_id: int
    match_id: int
    leaderboard: Leaderboard
    map_name: str
    won: bool | None
    rating_after_match: int | None
    rating_change: int | None


class Aoe2Coordinator(TimestampDataUpdateCoordinator[PlayerData]):
    config_entry: Aoe2ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: Aoe2ConfigEntry, client: AoeClient) -> None:
        self._update_intervals = get_update_intervals(entry.options)
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=self._update_intervals.usual,
        )
        self._client = client
        self._profile_id: int = entry.data[CONF_PROFILE_ID]
        self._recorded_matches = RecordedMatches(hass, entry.entry_id, self._profile_id)
        self._newly_recorded_matches: list[Match] = []

    @property
    def profile_id(self) -> int:
        return self._profile_id

    @property
    def client(self) -> AoeClient:
        return self._client

    async def _async_update_data(self) -> PlayerData:
        latest = await self._fetch_player_data()
        self._newly_recorded_matches = await self._record_new_matches(latest)
        self.update_interval = self._update_intervals.for_data(latest)
        return latest

    @callback
    def async_update_listeners(self) -> None:
        """Announce after entities update, so automations see the new ratings."""
        super().async_update_listeners()
        for match in self._newly_recorded_matches:
            event = get_match_finished_event(match, self._profile_id)
            self.hass.bus.async_fire(EVENT_MATCH_FINISHED, get_event_data(event))
        self._newly_recorded_matches = []

    async def _fetch_player_data(self) -> PlayerData:
        try:
            profile, matches = await asyncio.gather(
                self._client.get_profile(self._profile_id),
                self._client.get_recent_matches(self._profile_id, RECENT_MATCH_COUNT),
            )
        except AoeClientRetryError as error:
            raise UpdateFailed(str(error), retry_after=error.retry_after) from error
        except AoeClientError as error:
            raise UpdateFailed(str(error)) from error
        return PlayerData(profile=profile, matches=tuple(matches))

    async def _record_new_matches(self, latest: PlayerData) -> list[Match]:
        is_first_update = await self._player_was_just_added()
        unrecorded = get_unrecorded_matches(latest, self._recorded_matches)
        # Saving on the first update, even with nothing to record, marks the player as added.
        if unrecorded or is_first_update:
            await self._recorded_matches.async_record(match.match_id for match in unrecorded)
        return get_matches_to_announce(unrecorded, is_first_update)

    async def _player_was_just_added(self) -> bool:
        """A new entry has no saved record yet; one restarted after a reboot does."""
        if self._recorded_matches.is_loaded:
            return False
        found_saved_record = await self._recorded_matches.async_load()
        return not found_saved_record


def get_event_data(event: MatchFinishedEvent) -> MatchFinishedEventData:
    return MatchFinishedEventData(
        profile_id=event.profile_id,
        match_id=event.match_id,
        leaderboard=event.leaderboard,
        map_name=event.map_name,
        won=event.result.won,
        rating_after_match=event.result.rating_after_match,
        rating_change=event.result.rating_change,
    )


def get_update_intervals(options: Mapping[str, Any]) -> UpdateIntervals:
    return UpdateIntervals(
        usual=timedelta(minutes=options.get(CONF_UPDATE_MINUTES, MIN_UPDATE_MINUTES)),
        in_match=timedelta(
            minutes=options.get(CONF_IN_MATCH_UPDATE_MINUTES, MIN_IN_MATCH_UPDATE_MINUTES)
        ),
    )
