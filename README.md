# ha-aoe2

[![CI](https://github.com/AlexBramhill/ha-aoe2/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AlexBramhill/ha-aoe2/actions/workflows/ci.yml)
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz)

Home Assistant integration for Age of Empires II: Definitive Edition. Tracks player ratings and recent matches.

> **Status:** in development.

> **Unofficial project.** This is a community-made integration. It is not affiliated with, endorsed by or supported by [aoe2companion](https://www.aoe2companion.com), Microsoft, Xbox Game Studios, World's Edge or Forgotten Empires. Age of Empires is a trademark of Microsoft Corporation.

## Installation

Requires Home Assistant 2026.10 or later.

### HACS

[![Open your Home Assistant instance and open this repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=AlexBramhill&repository=ha-aoe2&category=integration)

Or add it by hand:

1. In HACS, open the menu and select **Custom repositories**.
2. Add `https://github.com/AlexBramhill/ha-aoe2` with the type **Integration**.
3. Search for **Age of Empires II** in HACS and download it.
4. Restart Home Assistant.

### Manual

1. Copy `custom_components/aoe2` into the `custom_components` folder of your Home Assistant configuration directory.
2. Restart Home Assistant.

## Configuration

[![Open your Home Assistant instance and start setting up Age of Empires II.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=aoe2)

Or set it up by hand:

1. Go to **Settings → Devices & services → Add integration** and select **Age of Empires II**.
2. Enter the player's profile ID. It is the number at the end of the player's profile address on [aoe2companion.com](https://www.aoe2companion.com), for example `196240`.

Each player is added as a separate entry and appears as its own device.

## Entities

### Sensors

Rating sensors are created for each leaderboard the player has a rating on, for example *RM 1v1* or *RM Team*. Sensors for a leaderboard the player starts playing later are added automatically.

| Entity | Enabled by default | Description |
|---|---|---|
| *Leaderboard* rating | Yes | Current rating. Recorded in long-term statistics. |
| *Leaderboard* rank | Yes | Current rank. Unknown when unranked. |
| *Leaderboard* wins, losses, games | No | Match counts on the leaderboard. |
| *Leaderboard* win rate | No | Percentage of games won. |
| *Leaderboard* streak | No | Current win or loss streak. |
| *Leaderboard* highest rating | No | Highest rating reached. |
| Last match result | Yes | `win` or `loss`. Attributes: leaderboard, map, civ, rating after the match, teammates, opponents. |
| Last match rating change | Yes | Rating change from the last match. |
| Last played | Yes | When the last match finished. |
| Last match map, civ | No | Map and civilisation of the last match. |
| Recent win rate | No | Win rate over the last five finished matches. |
| Recent rating change | No | Total rating change over the last five finished matches. |
| Last updated | Yes (diagnostic) | Time of the last successful update. |

### Binary sensor

| Entity | Description |
|---|---|
| In a match | On while the player has a match in progress. Attributes: leaderboard, map, start time. |

### Event

| Entity | Event types | Description |
|---|---|---|
| Match finished | `win`, `loss`, `unknown` | Fires when one of the player's matches finishes. Attributes include the match, leaderboard, map, rating after the match and rating change. |

The integration also fires an `aoe2_match_finished` event on the Home Assistant event bus with the same details. Matches played before the player was added are not announced, and each match is announced only once, including across restarts.

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

Replace `event.theviper_match_finished` with the entity ID shown for your player.

## Updates

Player data is refreshed every 10 minutes, and every 3 minutes while the player is in a match so results appear soon after a match ends.

To change these intervals, select **Configure** on the integration entry. The intervals cannot be set below 10 minutes, or 3 minutes during a match, to keep load on the data source low.

Automatic updates can be turned off in the integration entry's **System options**; the `homeassistant.update_entity` action refreshes the data on demand.

## Diagnostics

Select **Download diagnostics** on the integration entry to get data for a bug report. Profile IDs, player names, countries and match IDs are removed from the download.

## Data sources

| Name | Provider |
|---|---|
| `aoe2companion` | [aoe2companion.com](https://www.aoe2companion.com) |

Player data is provided by [aoe2companion](https://www.aoe2companion.com) through its public API. Thanks to the aoe2companion team for making it available. To keep load on their service low, the integration polls each player at most once every 3 minutes, and once every 10 minutes when the player is not in a match.

## Development

### Requirements

- Python 3.14.2 or later (required by Home Assistant 2026.10)
- [uv](https://docs.astral.sh/uv/)

### Setup

```sh
uv sync
```

This creates `.venv` and installs the locked dev dependencies from `uv.lock`.

### Checks

Run the test suite:

```sh
uv run pytest
```

Run the linter, formatter and type checks:

```sh
uv run ruff check
uv run ruff format --check
uv run pyright
```

CI also runs Home Assistant's `hassfest` and the HACS validation.

### Releasing

Releases are created by [release-please](https://github.com/googleapis/release-please) from commit messages on `main`, which follow [Conventional Commits](https://www.conventionalcommits.org):

| Commit prefix | Example | Release |
|---|---|---|
| `fix:` | `fix: keep rank when unranked` | Patch, for example 0.2.0 → 0.2.1 |
| `feat:` | `feat: add streak sensor` | Minor, for example 0.2.0 → 0.3.0 |
| `feat!:` or a `BREAKING CHANGE:` footer | `feat!: rename rating sensors` | Major once 1.0.0 is reached; minor before |
| `docs:`, `test:`, `ci:`, `chore:`, `refactor:` | `docs: explain profile IDs` | None |

After each push to `main`, release-please opens or updates a release pull request that bumps the version in `manifest.json` and `pyproject.toml` and updates `CHANGELOG.md`. Merging it tags the version and publishes the GitHub release that HACS offers to users.

### Querying the APIs

`scripts/try_api.py` queries a data source directly from the command line.

Fetch a player's ratings and recent matches by profile ID:

```sh
uv run python scripts/try_api.py aoe2companion <profile_id>
uv run python scripts/try_api.py aoe2companion <profile_id> --count 10
```
