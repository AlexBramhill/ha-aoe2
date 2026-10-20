"""Hit a real API from the command line.

    python scripts/try_api.py aoe2companion 196240
    python scripts/try_api.py worldsedge 196240
    python scripts/try_api.py aoe2companion --search TheViper
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import get_args

import aiohttp

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from custom_components.aoe2.api import ClientName, create_client


async def main(args: argparse.Namespace) -> None:
    async with aiohttp.ClientSession() as session:
        client = create_client(args.client, session)
        if args.search:
            for p in await client.search_players(args.search):
                print(p)
            return
        profile = await client.get_profile(args.profile_id)
        print(f"{profile.name} ({profile.country})")
        for r in profile.ratings:
            print(f"  {r.leaderboard:<10} {r.rating:>5}  rank={r.rank}  {r.wins}W/{r.losses}L")
        print("Recent matches:")
        for m in await client.get_recent_matches(args.profile_id, args.count):
            me = m.player_with_id(args.profile_id)
            result = {True: "WIN ", False: "LOSS", None: "?   "}[me.won if me else None]
            diff = f"{me.rating_change:+d}" if me and me.rating_change is not None else ""
            civ = (me.civ if me else None) or ""
            started = f"{m.started:%Y-%m-%d %H:%M}"
            print(f"  {started}  {result} {m.leaderboard}  {m.map_name}  {civ} {diff}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("client", choices=get_args(ClientName))
    parser.add_argument("profile_id", type=int, nargs="?")
    parser.add_argument("--search")
    parser.add_argument("--count", type=int, default=5)
    asyncio.run(main(parser.parse_args()))
