# ha-aoe2

[![CI](https://github.com/AlexBramhill/ha-aoe2/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/AlexBramhill/ha-aoe2/actions/workflows/ci.yml)
[![Python 3.14+](https://img.shields.io/badge/python-3.14%2B-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Home Assistant integration for Age of Empires II: Definitive Edition. Tracks player ratings and recent matches.

> **Status:** in development.

## Requirements

- Python 3.14.2 or later (required by Home Assistant 2026.10)
- [uv](https://docs.astral.sh/uv/)

## Setup

```sh
uv sync
```

This creates `.venv` and installs the locked dev dependencies from `uv.lock`.

## Development

Run the test suite:

```sh
uv run pytest
```

Run the linter and formatter checks:

```sh
uv run ruff check
uv run ruff format --check
```

## Querying the APIs

`scripts/try_api.py` queries a data source directly from the command line.

Fetch a player's ratings and recent matches by profile ID:

```sh
uv run python scripts/try_api.py aoe2companion <profile_id>
uv run python scripts/try_api.py aoe2companion <profile_id> --count 10
```

## Data sources

| Name | Provider |
|---|---|
| `aoe2companion` | [aoe2companion.com](https://www.aoe2companion.com) |
