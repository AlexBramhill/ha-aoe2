import json
from dataclasses import asdict
from datetime import timedelta
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant
from homeassistant.helpers.json import json_dumps

from .coordinator import Aoe2ConfigEntry

IDENTIFYING_KEYS = {"profile_id", "name", "title", "unique_id", "country", "match_id"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: Aoe2ConfigEntry
) -> dict[str, Any]:
    coordinator = entry.runtime_data
    return async_redact_data(
        {
            "entry": entry.as_dict(),
            "coordinator": {
                "last_update_success": coordinator.last_update_success,
                "last_update_success_time": coordinator.last_update_success_time,
                "update_interval_seconds": _seconds(coordinator.update_interval),
            },
            "data": _as_json_data(asdict(coordinator.data)),
        },
        IDENTIFYING_KEYS,
    )


def _as_json_data(value: Any) -> Any:
    """Tuples become lists, so redaction reaches inside them."""
    return json.loads(json_dumps(value))


def _seconds(interval: timedelta | None) -> float | None:
    return None if interval is None else interval.total_seconds()
