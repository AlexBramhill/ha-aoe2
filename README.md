# ha-aoe2

[![CI](https://github.com/AlexBramhill/ha-aoe2/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AlexBramhill/ha-aoe2/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/AlexBramhill/ha-aoe2?include_prereleases)](https://github.com/AlexBramhill/ha-aoe2/releases)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)

Home Assistant integration that tracks Age of Empires II: Definitive Edition player ratings and matches.

> **Status:** in development.

## Installation

Requires Home Assistant 2026.10 or later.

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=AlexBramhill&repository=ha-aoe2&category=integration)

Or add `https://github.com/AlexBramhill/ha-aoe2` to HACS as a custom Integration repository, download `Age of Empires II` and restart Home Assistant.

## Configuration

[![Open your Home Assistant instance and start setting up Age of Empires II.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=aoe2)

Or go to **Settings → Devices & services → Add integration → Age of Empires II**.

Enter the player's profile ID, the number at the end of their [aoe2companion.com](https://www.aoe2companion.com) profile address (for example `196240`). Add one entry per player. **Reconfigure** switches an entry to another player.

**Configure** changes how often data refreshes: every 10 minutes by default, or every 3 minutes during a match.

## Entities

Rating sensors are created for each leaderboard the player plays, such as *RM 1v1* or *RM Team*.

| Entity                            | Enabled by default | Description                                                                 |
|-----------------------------------|--------------------|-----------------------------------------------------------------------------|
| *Leaderboard* rating, rank        | Yes                | Current rating and rank.                                                    |
| *Leaderboard* wins, losses, games | No                 | Match counts.                                                               |
| *Leaderboard* win rate, streak    | No                 | Percentage of games won and current streak.                                 |
| *Leaderboard* highest rating      | No                 | Highest rating reached.                                                     |
| Last match result                 | Yes                | `win` or `loss`, with map, civ, teammates and opponents as attributes.      |
| Last match rating change          | Yes                | Rating change from the last match.                                          |
| Last played                       | Yes                | When the last match finished.                                               |
| Last match map, civ               | No                 | Map and civilisation of the last match.                                     |
| Recent win rate, rating change    | No                 | Over the last five matches.                                                 |
| In a match                        | Yes                | On while a match is in progress.                                            |
| Match finished                    | Yes                | Event entity that fires `win`, `loss` or `unknown` when a match ends.       |

### Example automation

```yaml
automation:
  - alias: "Announce Age of Empires II results"
    triggers:
      - trigger: state
        entity_id: event.theviper_match_finished
    actions:
      - action: notify.notify
        data:
          message: >
            {{ trigger.to_state.attributes.event_type | title }}!
            New rating: {{ trigger.to_state.attributes.rating_after_match }}
            ({{ trigger.to_state.attributes.rating_change }}).
```

## Credits

Player data comes from [aoe2companion](https://www.aoe2companion.com), created by [denniske](https://github.com/denniske). 

If you find this useful, consider supporting them: get the app on the [App Store](https://apps.apple.com/app/id1518463195) or [Google Play](https://play.google.com/store/apps/details?id=com.aoe2companion), join the [Discord](https://discord.gg/gCunWKx) or [buy denniske a coffee](https://www.buymeacoffee.com/denniskeil).

## Disclaimer

This is an unofficial community project. 

aoe2companion is an independent project that provides the data but doesn't endorse or support this integration, so please report problems here.

Age of Empires is a trademark of Microsoft Corporation; neither this integration nor aoe2companion is made, endorsed or supported by Microsoft, Xbox Game Studios, World's Edge or Forgotten Empires.

## Development

Requires Python 3.14.2+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
uv run pytest
uv run ruff check && uv run ruff format --check && uv run pyright
uv run python scripts/try_api.py aoe2companion <profile_id>  # query the API directly
```

Commits follow [Conventional Commits](https://www.conventionalcommits.org); releases are created by release-please.

## License

[MIT](LICENSE)
