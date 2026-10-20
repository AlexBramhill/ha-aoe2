"""Query a data source from the command line.

    python scripts/try_api.py aoe2companion <profile_id>
    python scripts/try_api.py worldsedge <profile_id> --count 10
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import get_args

import aiohttp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.aoe2.api import (
    AoeClient,
    ClientName,
    Match,
    MatchPlayer,
    Profile,
    Rating,
    create_client,
)


async def main(args: argparse.Namespace) -> None:
    async with aiohttp.ClientSession() as session:
        client = create_client(args.client, session)
        await print_player(client, args.profile_id, args.count)


async def print_player(client: AoeClient, profile_id: int, match_count: int) -> None:
    profile = await client.get_profile(profile_id)
    matches = await client.get_recent_matches(profile_id, match_count)

    print(format_profile_heading(profile))
    for rating in profile.ratings:
        print(format_rating(rating))

    print("Recent matches:")
    for match in matches:
        print(format_match(match, profile_id))


def format_profile_heading(profile: Profile) -> str:
    return f"{profile.name} ({profile.country or '?'})"


def format_rating(rating: Rating) -> str:
    record = f"{rating.wins}W/{rating.losses}L"
    return f"  {rating.leaderboard:<10} {rating.rating:>5}  rank={rating.rank}  {record}"


def format_match(match: Match, profile_id: int) -> str:
    player = match.player_with_id(profile_id)
    columns = [
        f"{match.started:%Y-%m-%d %H:%M}",
        format_result(player),
        str(match.leaderboard),
        match.map_name or "",
        format_civ(player),
        format_rating_change(player),
    ]
    return "  " + "  ".join(columns)


def format_result(player: MatchPlayer | None) -> str:
    if player is None or player.won is None:
        return "?   "
    return "WIN " if player.won else "LOSS"


def format_civ(player: MatchPlayer | None) -> str:
    if player is None or player.civ is None:
        return ""
    return player.civ


def format_rating_change(player: MatchPlayer | None) -> str:
    if player is None or player.rating_change is None:
        return ""
    return f"{player.rating_change:+d}"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Query an AoE2 data source.")
    parser.add_argument("client", choices=get_args(ClientName), help="data source to query")
    parser.add_argument("profile_id", type=int, help="player to show")
    parser.add_argument(
        "--count", type=int, default=5, help="maximum number of recent matches to show"
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main(parse_args()))
