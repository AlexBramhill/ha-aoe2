from dataclasses import asdict
from datetime import timedelta

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import json_dumps
from homeassistant.util.json import JsonValueType, json_loads

from custom_components.aoe2.ha import Aoe2ConfigEntry

IDENTIFYING_KEYS = {"profile_id", "name", "title", "unique_id", "country", "match_id"}


async def async_get_config_entry_diagnostics(
    _hass: HomeAssistant, entry: Aoe2ConfigEntry
) -> dict[str, object]:
    coordinator = entry.runtime_data
    # HA types the Mapping overload as returning a bare dict
    return async_redact_data(  # pyright: ignore[reportUnknownVariableType]
        {
            "entry": entry.as_dict(),
            "coordinator": {
                "last_update_success": coordinator.last_update_success,
                "last_update_success_time": coordinator.last_update_success_time,
                "update_interval_seconds": _get_seconds(coordinator.update_interval),
            },
            "data": _get_json_data(asdict(coordinator.data)),
        },
        IDENTIFYING_KEYS,
    )


def _get_json_data(value: object) -> JsonValueType:
    """Tuples become lists, so redaction reaches inside them."""
    return json_loads(json_dumps(value))


def _get_seconds(interval: timedelta | None) -> float | None:
    return None if interval is None else interval.total_seconds()
