import json
from pathlib import Path
from typing import Any

FIXTURES = Path(__file__).parent / "fixtures"

VIPER_PROFILE_ID = 196240


def read_fixture(name: str) -> Any:
    return json.loads((FIXTURES / name).read_text())
