from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, EntityCategory
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .api import Leaderboard, Match, MatchPlayer, Rating
from .coordinator import Aoe2ConfigEntry, Aoe2Coordinator, Aoe2Data
from .entity import Aoe2Entity

PARALLEL_UPDATES = 0

RESULT_WIN = "win"
RESULT_LOSS = "loss"

LEADERBOARD_NAMES: dict[Leaderboard, str] = {
    Leaderboard.RM_1V1: "RM 1v1",
    Leaderboard.RM_TEAM: "RM Team",
    Leaderboard.EW_1V1: "EW 1v1",
    Leaderboard.EW_TEAM: "EW Team",
    Leaderboard.QP_RM_1V1: "Quick Play RM 1v1",
    Leaderboard.QP_RM_TEAM: "Quick Play RM Team",
    Leaderboard.DM_1V1: "DM 1v1",
    Leaderboard.DM_TEAM: "DM Team",
    Leaderboard.UNRANKED: "Unranked",
    Leaderboard.RM_1V1_CONSOLE: "RM 1v1 (console)",
    Leaderboard.RM_TEAM_CONSOLE: "RM Team (console)",
    Leaderboard.EW_1V1_CONSOLE: "EW 1v1 (console)",
    Leaderboard.EW_TEAM_CONSOLE: "EW Team (console)",
}

type SensorValue = StateType | datetime


@dataclass(frozen=True, kw_only=True)
class Aoe2RatingSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[Rating], SensorValue]


@dataclass(frozen=True, kw_only=True)
class Aoe2PlayerSensorEntityDescription(SensorEntityDescription):
    value_fn: Callable[[Aoe2Data], SensorValue]
    attributes_fn: Callable[[Aoe2Data], dict[str, Any]] | None = None


RATING_SENSORS: tuple[Aoe2RatingSensorEntityDescription, ...] = (
    Aoe2RatingSensorEntityDescription(
        key="rating",
        translation_key="rating",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda rating: rating.rating,
    ),
    Aoe2RatingSensorEntityDescription(
        key="rank",
        translation_key="rank",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda rating: rating.rank,
    ),
    Aoe2RatingSensorEntityDescription(
        key="wins",
        translation_key="wins",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
        value_fn=lambda rating: rating.wins,
    ),
    Aoe2RatingSensorEntityDescription(
        key="losses",
        translation_key="losses",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
        value_fn=lambda rating: rating.losses,
    ),
    Aoe2RatingSensorEntityDescription(
        key="games",
        translation_key="games",
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=False,
        value_fn=lambda rating: rating.games,
    ),
    Aoe2RatingSensorEntityDescription(
        key="win_rate",
        translation_key="win_rate",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        entity_registry_enabled_default=False,
        value_fn=lambda rating: _get_percentage(rating.win_rate),
    ),
    Aoe2RatingSensorEntityDescription(
        key="streak",
        translation_key="streak",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda rating: rating.streak,
    ),
    Aoe2RatingSensorEntityDescription(
        key="highest_rating",
        translation_key="highest_rating",
        entity_registry_enabled_default=False,
        value_fn=lambda rating: rating.highest_rating,
    ),
)


def get_last_match_result(data: Aoe2Data) -> str | None:
    return _get_from_last_match(data, lambda match: _get_result(data.player_in(match)))


def get_last_match_rating_change(data: Aoe2Data) -> int | None:
    return _get_from_last_match(data, lambda match: data.player_in(match).rating_change)


def get_last_played(data: Aoe2Data) -> datetime | None:
    return _get_from_last_match(data, lambda match: match.finished)


def get_last_match_map(data: Aoe2Data) -> str | None:
    return _get_from_last_match(data, lambda match: match.map_name)


def get_last_match_civ(data: Aoe2Data) -> str | None:
    return _get_from_last_match(data, lambda match: data.player_in(match).civ)


def get_last_match_details(data: Aoe2Data) -> dict[str, Any]:
    match = data.last_finished_match()
    if match is None:
        return {}
    player = data.player_in(match)
    return {
        "leaderboard": match.leaderboard,
        "map": match.map_name,
        "civ": player.civ,
        "rating_after_match": player.rating_after_match,
        "teammates": _get_teammates(match, player),
        "opponents": _get_opponents(match, player),
    }


def get_recent_win_rate(data: Aoe2Data) -> float | None:
    results = [data.player_in(match).won for match in data.finished_matches()]
    known_results = [won for won in results if won is not None]
    if not known_results:
        return None
    return _get_percentage(known_results.count(True) / len(known_results))


def get_recent_rating_change(data: Aoe2Data) -> int | None:
    changes = [data.player_in(match).rating_change for match in data.finished_matches()]
    known_changes = [change for change in changes if change is not None]
    return sum(known_changes) if known_changes else None


PLAYER_SENSORS: tuple[Aoe2PlayerSensorEntityDescription, ...] = (
    Aoe2PlayerSensorEntityDescription(
        key="last_match_result",
        translation_key="last_match_result",
        device_class=SensorDeviceClass.ENUM,
        options=[RESULT_WIN, RESULT_LOSS],
        value_fn=get_last_match_result,
        attributes_fn=get_last_match_details,
    ),
    Aoe2PlayerSensorEntityDescription(
        key="last_match_rating_change",
        translation_key="last_match_rating_change",
        value_fn=get_last_match_rating_change,
    ),
    Aoe2PlayerSensorEntityDescription(
        key="last_played",
        translation_key="last_played",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=get_last_played,
    ),
    Aoe2PlayerSensorEntityDescription(
        key="last_match_map",
        translation_key="last_match_map",
        entity_registry_enabled_default=False,
        value_fn=get_last_match_map,
    ),
    Aoe2PlayerSensorEntityDescription(
        key="last_match_civ",
        translation_key="last_match_civ",
        entity_registry_enabled_default=False,
        value_fn=get_last_match_civ,
    ),
    Aoe2PlayerSensorEntityDescription(
        key="recent_win_rate",
        translation_key="recent_win_rate",
        native_unit_of_measurement=PERCENTAGE,
        suggested_display_precision=0,
        entity_registry_enabled_default=False,
        value_fn=get_recent_win_rate,
    ),
    Aoe2PlayerSensorEntityDescription(
        key="recent_rating_change",
        translation_key="recent_rating_change",
        entity_registry_enabled_default=False,
        value_fn=get_recent_rating_change,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: Aoe2ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            *(Aoe2PlayerSensor(coordinator, description) for description in PLAYER_SENSORS),
            Aoe2LastUpdatedSensor(coordinator),
        ]
    )
    rating_sensors = RatingSensorsPerLeaderboard(coordinator, async_add_entities)
    rating_sensors.add_for_new_leaderboards()
    entry.async_on_unload(coordinator.async_add_listener(rating_sensors.add_for_new_leaderboards))


class Aoe2RatingSensor(Aoe2Entity, SensorEntity):
    entity_description: Aoe2RatingSensorEntityDescription

    def __init__(
        self,
        coordinator: Aoe2Coordinator,
        description: Aoe2RatingSensorEntityDescription,
        leaderboard: Leaderboard,
    ) -> None:
        super().__init__(coordinator, f"{leaderboard}_{description.key}")
        self.entity_description = description
        self._leaderboard = leaderboard
        self._attr_translation_placeholders = {"leaderboard": LEADERBOARD_NAMES[leaderboard]}

    @property
    def native_value(self) -> SensorValue:
        rating = self.coordinator.data.profile.rating_for(self._leaderboard)
        return None if rating is None else self.entity_description.value_fn(rating)


class Aoe2PlayerSensor(Aoe2Entity, SensorEntity):
    entity_description: Aoe2PlayerSensorEntityDescription

    def __init__(
        self, coordinator: Aoe2Coordinator, description: Aoe2PlayerSensorEntityDescription
    ) -> None:
        super().__init__(coordinator, description.key)
        self.entity_description = description

    @property
    def native_value(self) -> SensorValue:
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        attributes_fn = self.entity_description.attributes_fn
        return None if attributes_fn is None else attributes_fn(self.coordinator.data)


class Aoe2LastUpdatedSensor(Aoe2Entity, SensorEntity):
    _attr_translation_key = "last_updated"
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: Aoe2Coordinator) -> None:
        super().__init__(coordinator, "last_updated")

    @property
    def native_value(self) -> datetime | None:
        return self.coordinator.last_update_success_time


class RatingSensorsPerLeaderboard:
    def __init__(
        self, coordinator: Aoe2Coordinator, async_add_entities: AddConfigEntryEntitiesCallback
    ) -> None:
        self._coordinator = coordinator
        self._async_add_entities = async_add_entities
        self._leaderboards_with_sensors: set[Leaderboard] = set()

    @callback
    def add_for_new_leaderboards(self) -> None:
        new_leaderboards = self._get_leaderboards_without_sensors()
        self._leaderboards_with_sensors.update(new_leaderboards)
        self._async_add_entities(self._get_sensors_for(new_leaderboards))

    def _get_leaderboards_without_sensors(self) -> list[Leaderboard]:
        return [
            rating.leaderboard
            for rating in self._coordinator.data.profile.ratings
            if rating.leaderboard in LEADERBOARD_NAMES
            and rating.leaderboard not in self._leaderboards_with_sensors
        ]

    def _get_sensors_for(self, leaderboards: list[Leaderboard]) -> list[Aoe2RatingSensor]:
        return [
            Aoe2RatingSensor(self._coordinator, description, leaderboard)
            for leaderboard in leaderboards
            for description in RATING_SENSORS
        ]


def _get_from_last_match[Value](data: Aoe2Data, value_of: Callable[[Match], Value]) -> Value | None:
    match = data.last_finished_match()
    return None if match is None else value_of(match)


def _get_result(player: MatchPlayer) -> str | None:
    if player.won is None:
        return None
    return RESULT_WIN if player.won else RESULT_LOSS


def _get_teammates(match: Match, player: MatchPlayer) -> list[str]:
    return [
        other.name
        for other in match.players
        if other.team == player.team and other.profile_id != player.profile_id
    ]


def _get_opponents(match: Match, player: MatchPlayer) -> list[str]:
    return [other.name for other in match.players if other.team != player.team]


def _get_percentage(fraction: float | None) -> float | None:
    return None if fraction is None else round(fraction * 100, 1)
