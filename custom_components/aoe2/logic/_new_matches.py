from collections.abc import Container

from custom_components.aoe2.api import Match
from custom_components.aoe2.logic._player_data import PlayerData


def get_unrecorded_matches(data: PlayerData, recorded_ids: Container[int]) -> list[Match]:
    finished_oldest_first = reversed(data.finished_matches())
    return [match for match in finished_oldest_first if match.match_id not in recorded_ids]


def get_matches_to_announce(unrecorded: list[Match], is_first_update: bool) -> list[Match]:
    return [] if is_first_update else unrecorded
