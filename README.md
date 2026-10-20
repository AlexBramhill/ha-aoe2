# ha-aoe2

A Home Assistant integration for Age of Empires II: DE. It tracks a player's Elo and their latest games.

> Work in progress. The API layer is done; the Home Assistant side (coordinator, config flow, sensors) is next.

## Getting going

You need Python 3.13 or newer.

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install --group dev
```

Run the tests:

```sh
pytest
```

Lint:

```sh
ruff check
```

## Try it against the real APIs

You'll need a profile ID. Search for one by name:

```sh
python scripts/try_api.py aoe2companion --search TheViper
```

Then pull ratings and recent games:

```sh
python scripts/try_api.py aoe2companion 196240
python scripts/try_api.py worldsedge 196240 --count 10
```

## Data sources

There are two, and both use the same profile IDs:

- **aoe2companion** is the default. It has a good name search and gives civ and map names.
- **worldsedge** is the official (but undocumented) Relic/World's Edge API. Its search only matches exact in-game names, and it returns civs as IDs only.

## Layout

```
custom_components/aoe2/api/   # API clients, no Home Assistant imports
  client.py                   # AoeClient protocol both clients follow
  aoe2companion.py            # aoe2companion client + parsers
  worldsedge.py               # World's Edge client + parsers
  models.py                   # Profile, Rating, Match, ...
  errors.py                   # AoeClient*Error types
tests/                        # parser tests against saved real responses
scripts/try_api.py            # poke the live APIs from the terminal
```
