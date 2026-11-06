"""Typed reads of JSON and other nested data tests inspect."""

from pathlib import Path
from typing import TypeIs

from homeassistant.util.json import JsonValueType, json_loads


def read_json(path: Path) -> JsonValueType:
    return json_loads(path.read_text())


def read_json_object(path: Path) -> dict[str, object]:
    value = read_json(path)
    assert is_dict(value), f"{path} is not a JSON object"
    return value


def get_at(value: object, *path: str | int) -> object:
    for step in path:
        value = _get_child(value, step)
    return value


def get_object_at(value: object, *path: str | int) -> dict[str, object]:
    found = get_at(value, *path)
    assert is_dict(found), f"Expected an object at {path}, got {found!r}"
    return found


def get_list_at(value: object, *path: str | int) -> list[object]:
    found = get_at(value, *path)
    assert is_list(found), f"Expected a list at {path}, got {found!r}"
    return found


def is_dict(value: object) -> TypeIs[dict[str, object]]:
    return isinstance(value, dict)


def is_list(value: object) -> TypeIs[list[object]]:
    return isinstance(value, list)


def _get_child(value: object, step: str | int) -> object:
    if isinstance(step, str) and is_dict(value):
        return value[step]
    if isinstance(step, int) and is_list(value):
        return value[step]
    raise AssertionError(f"Cannot read {step!r} from {value!r}")
