import asyncio
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Self, TypedDict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import TimestampDataUpdateCoordinator, UpdateFailed

from .api import (
    AoeClient,
    AoeClientError,
    AoeClientRetryError,
    Leaderboard,
    Match,
    MatchPlayer,
    Profile,
)
from .const import (
    CONF_IN_MATCH_UPDATE_MINUTES,
    CONF_PROFILE_ID,
    CONF_UPDATE_MINUTES,
    DOMAIN,
    EVENT_MATCH_FINISHED,
    LOGGER,
    MIN_IN_MATCH_UPDATE_MINUTES,
    MIN_UPDATE_MINUTES,
)
from .recorded_matches import RecordedMatches

RECENT_MATCH_COUNT = 5

type Aoe2ConfigEntry = ConfigEntry[Aoe2Coordinator]


class PlayerResult(TypedDict):
    won: bool | None
    rating_after_match: int | None
    rating_change: int | None


class MatchFinishedEvent(PlayerResult):
    profile_id: int
    match_id: int
    leaderboard: Leaderboard
    map_name: str


@dataclass(frozen=True, slots=True)
class UpdateIntervals:
    usual: timedelta
    in_match: timedelta

    @classmethod
    def from_options(cls, options: Mapping[str, Any]) -> Self:
        return cls(
            usual=timedelta(minutes=options.get(CONF_UPDATE_MINUTES, MIN_UPDATE_MINUTES)),
            in_match=timedelta(
                minutes=options.get(CONF_IN_MATCH_UPDATE_MINUTES, MIN_IN_MATCH_UPDATE_MINUTES)
            ),
        )

    def for_data(self, data: Aoe2Data) -> timedelta:
        return self.usual if data.current_match() is None else self.in_match


@dataclass(frozen=True, slots=True)
class Aoe2Data:
    profile: Profile
    matches: tuple[Match, ...]

    def finished_matches(self) -> tuple[Match, ...]:
        return tuple(match for match in self.matches if match.finished is not None)

    def last_finished_match(self) -> Match | None:
        return next(iter(self.finished_matches()), None)

    def current_match(self) -> Match | None:
        return next((match for match in self.matches if match.finished is None), None)

    def player_in(self, match: Match) -> MatchPlayer:
        return match.player_with_id(self.profile.profile_id)


class Aoe2Coordinator(TimestampDataUpdateCoordinator[Aoe2Data]):
    config_entry: Aoe2ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: Aoe2ConfigEntry, client: AoeClient) -> None:
        self._update_intervals = UpdateIntervals.from_options(entry.options)
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

    async def _async_update_data(self) -> Aoe2Data:
        latest = await self._fetch_player_data()
        self._newly_recorded_matches = await self._record_new_matches(latest)
        self.update_interval = self._update_intervals.for_data(latest)
        return latest

    @callback
    def async_update_listeners(self) -> None:
        """Announce after entities update, so automations see the new ratings."""
        super().async_update_listeners()
        for match in self._newly_recorded_matches:
            self.hass.bus.async_fire(EVENT_MATCH_FINISHED, self._get_match_event_data(match))
        self._newly_recorded_matches = []

    async def _fetch_player_data(self) -> Aoe2Data:
        try:
            profile, matches = await asyncio.gather(
                self._client.get_profile(self._profile_id),
                self._client.get_recent_matches(self._profile_id, RECENT_MATCH_COUNT),
            )
        except AoeClientRetryError as error:
            raise UpdateFailed(str(error), retry_after=error.retry_after) from error
        except AoeClientError as error:
            raise UpdateFailed(str(error)) from error
        return Aoe2Data(profile=profile, matches=tuple(matches))

    async def _record_new_matches(self, latest: Aoe2Data) -> list[Match]:
        finished_oldest_first = list(reversed(latest.finished_matches()))
        if await self._player_was_just_added():
            await self._record_without_announcing(finished_oldest_first)
            return []
        new_matches = self._get_not_yet_recorded(finished_oldest_first)
        if new_matches:
            await self._recorded_matches.async_record(match.match_id for match in new_matches)
        return new_matches

    async def _player_was_just_added(self) -> bool:
        """A new entry has no saved record yet; one restarted after a reboot does."""
        if self._recorded_matches.is_loaded:
            return False
        found_saved_record = await self._recorded_matches.async_load()
        return not found_saved_record

    async def _record_without_announcing(self, past_matches: list[Match]) -> None:
        """Games played before the player was added are history, not news."""
        await self._recorded_matches.async_record(match.match_id for match in past_matches)

    def _get_not_yet_recorded(self, matches: list[Match]) -> list[Match]:
        return [match for match in matches if match.match_id not in self._recorded_matches]

    def _get_match_event_data(self, match: Match) -> MatchFinishedEvent:
        return MatchFinishedEvent(
            profile_id=self._profile_id,
            match_id=match.match_id,
            leaderboard=match.leaderboard,
            map_name=match.map_name,
            **_get_player_result(match.player_with_id(self._profile_id)),
        )


def _get_player_result(player: MatchPlayer) -> PlayerResult:
    return PlayerResult(
        won=player.won,
        rating_after_match=player.rating_after_match,
        rating_change=player.rating_change,
    )
