# ha-aoe2

[![Tests](https://github.com/AlexBramhill/ha-aoe2/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/AlexBramhill/ha-aoe2/actions/workflows/tests.yml)
[![Lint](https://github.com/AlexBramhill/ha-aoe2/actions/workflows/lint.yml/badge.svg?branch=main)](https://github.com/AlexBramhill/ha-aoe2/actions/workflows/lint.yml)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Home Assistant integration for Age of Empires II: Definitive Edition. Tracks player ratings and recent matches.

> **Status:** in development.

## Requirements

- Python 3.13 or later

## Setup

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install --group dev
```

## Development

Run the test suite:

```sh
pytest
```

Run the linter:

```sh
ruff check
```

## Querying the APIs

`scripts/try_api.py` queries a data source directly from the command line.

Fetch a player's ratings and recent matches by profile ID:

```sh
python scripts/try_api.py aoe2companion <profile_id>
python scripts/try_api.py worldsedge <profile_id> --count 10
```

## Data sources

| Name | Provider |
|---|---|
| `aoe2companion` | [aoe2companion.com](https://www.aoe2companion.com) |
| `worldsedge` | Relic / World's Edge community API |
