import asyncio
from dataclasses import dataclass
from datetime import timedelta
from typing import TypedDict

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    AoeClient,
    AoeClientError,
    AoeClientRateLimitError,
    Leaderboard,
    Match,
    MatchPlayer,
    Profile,
)
from .const import CONF_PROFILE_ID, DOMAIN, EVENT_MATCH_FINISHED, LOGGER

UPDATE_INTERVAL = timedelta(minutes=10)
RECENT_MATCH_COUNT = 5

type Aoe2ConfigEntry = ConfigEntry[Aoe2Coordinator]


class PlayerResult(TypedDict):
    won: bool | None
    rating_after_match: int | None
    rating_change: int | None


class MatchFinishedEvent(PlayerResult):
    profile_id: int
    match_id: int
    leaderboard: Leaderboard | None
    map_name: str | None


@dataclass(frozen=True, slots=True)
class Aoe2Data:
    profile: Profile
    matches: tuple[Match, ...]

    def finished_match_ids(self) -> set[int]:
        return {match.match_id for match in self.matches if match.finished is not None}


class Aoe2Coordinator(DataUpdateCoordinator[Aoe2Data]):
    config_entry: Aoe2ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: Aoe2ConfigEntry, client: AoeClient) -> None:
        super().__init__(
            hass,
            LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self._client = client
        self._profile_id: int = entry.data[CONF_PROFILE_ID]

    async def _async_update_data(self) -> Aoe2Data:
        latest = await self._fetch_player_data()
        if self.data is not None:
            self._announce_newly_finished_matches(self.data, latest)
        return latest

    async def _fetch_player_data(self) -> Aoe2Data:
        try:
            profile, matches = await asyncio.gather(
                self._client.get_profile(self._profile_id),
                self._client.get_recent_matches(self._profile_id, RECENT_MATCH_COUNT),
            )
        except AoeClientRateLimitError as error:
            raise UpdateFailed(str(error), retry_after=error.retry_after) from error
        except AoeClientError as error:
            raise UpdateFailed(str(error)) from error
        return Aoe2Data(profile=profile, matches=tuple(matches))

    def _announce_newly_finished_matches(self, previous: Aoe2Data, latest: Aoe2Data) -> None:
        for match in _newly_finished_matches_oldest_first(previous, latest):
            self.hass.bus.async_fire(EVENT_MATCH_FINISHED, self._match_event_data(match))

    def _match_event_data(self, match: Match) -> MatchFinishedEvent:
        return MatchFinishedEvent(
            profile_id=self._profile_id,
            match_id=match.match_id,
            leaderboard=match.leaderboard,
            map_name=match.map_name,
            **_player_result(match.player_with_id(self._profile_id)),
        )


def _newly_finished_matches_oldest_first(previous: Aoe2Data, latest: Aoe2Data) -> list[Match]:
    already_announced = previous.finished_match_ids()
    newest_first = [
        match
        for match in latest.matches
        if match.finished is not None and match.match_id not in already_announced
    ]
    return list(reversed(newest_first))


def _player_result(player: MatchPlayer | None) -> PlayerResult:
    if player is None:
        return PlayerResult(won=None, rating_after_match=None, rating_change=None)
    return PlayerResult(
        won=player.won,
        rating_after_match=player.rating_after_match,
        rating_change=player.rating_change,
    )
