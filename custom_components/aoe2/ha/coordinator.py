import asyncio
from collections.abc import Callable, Mapping
from dataclasses import asdict
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.update_coordinator import TimestampDataUpdateCoordinator, UpdateFailed

from custom_components.aoe2.api import AoeClient, AoeClientError, AoeClientRetryError
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
from custom_components.aoe2.ha.recorded_matches import RecordedMatches
from custom_components.aoe2.logic import (
    MatchFinishedEvent,
    MatchLedger,
    UpdateIntervals,
    get_match_finished_event,
    get_new_matches,
)
from custom_components.aoe2.models import Match, PlayerData

RECENT_MATCH_COUNT = 5

type MatchFinishedListener = Callable[[MatchFinishedEvent], None]


class Aoe2Coordinator(TimestampDataUpdateCoordinator[PlayerData]):
    config_entry: ConfigEntry[Aoe2Coordinator]

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry[Aoe2Coordinator], client: AoeClient
    ) -> None:
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
        self._recorded_matches = RecordedMatches(hass, entry.entry_id)
        self._ledger: MatchLedger | None = None
        self._matches_to_announce: list[Match] = []
        self._match_finished_listeners: list[MatchFinishedListener] = []

    @property
    def profile_id(self) -> int:
        return self._profile_id

    @property
    def client(self) -> AoeClient:
        return self._client

    @callback
    def async_add_match_finished_listener(self, listener: MatchFinishedListener) -> CALLBACK_TYPE:
        self._match_finished_listeners.append(listener)

        @callback
        def remove_listener() -> None:
            self._match_finished_listeners.remove(listener)

        return remove_listener

    async def _async_setup(self) -> None:
        self._ledger = await self._recorded_matches.async_load()

    async def _async_update_data(self) -> PlayerData:
        latest = await self._fetch_player_data()
        self._matches_to_announce = await self._record_new_matches(latest)
        self.update_interval = self._update_intervals.for_data(latest)
        return latest

    @callback
    def async_update_listeners(self) -> None:
        """Announce after entities update, so automations see the new ratings."""
        super().async_update_listeners()
        for match in self._matches_to_announce:
            event = get_match_finished_event(match, self._profile_id)
            for listener in self._match_finished_listeners:
                listener(event)
            self.hass.bus.async_fire(EVENT_MATCH_FINISHED, asdict(event))
        self._matches_to_announce = []

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
        # Todo: refactor this nicer
        check = get_new_matches(latest, self._ledger)
        if check.ledger != self._ledger:
            await self._recorded_matches.async_save(check.ledger)
        self._ledger = check.ledger
        return check.to_announce


def get_update_intervals(options: Mapping[str, Any]) -> UpdateIntervals:
    return UpdateIntervals(
        usual=timedelta(minutes=options.get(CONF_UPDATE_MINUTES, MIN_UPDATE_MINUTES)),
        in_match=timedelta(
            minutes=options.get(CONF_IN_MATCH_UPDATE_MINUTES, MIN_IN_MATCH_UPDATE_MINUTES)
        ),
    )
