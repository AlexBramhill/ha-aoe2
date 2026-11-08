from collections.abc import Mapping
from typing import ClassVar, Self

from homeassistant.config_entries import ConfigEntry
from pydantic import BaseModel, ConfigDict

from custom_components.aoe2.api import ClientName
from custom_components.aoe2.const import (
    DEFAULT_CLIENT,
    MIN_IN_MATCH_UPDATE_MINUTES,
    MIN_UPDATE_MINUTES,
)


class _Stored(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(strict=True, frozen=True)

    @classmethod
    def from_mapping(cls, values: Mapping[str, object]) -> Self:
        return cls.model_validate(dict(values))


class EntryData(_Stored):
    profile_id: int
    client: ClientName = DEFAULT_CLIENT

    @classmethod
    def from_entry(cls, entry: ConfigEntry) -> Self:
        return cls.from_mapping(entry.data)


class EntryOptions(_Stored):
    update_minutes: int = MIN_UPDATE_MINUTES
    in_match_update_minutes: int = MIN_IN_MATCH_UPDATE_MINUTES

    @classmethod
    def from_entry(cls, entry: ConfigEntry) -> Self:
        return cls.from_mapping(entry.options)
