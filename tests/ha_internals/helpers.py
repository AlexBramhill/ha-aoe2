import json
from pathlib import Path

MANIFEST = Path(__file__).parents[2] / "custom_components/aoe2/manifest.json"


def read_manifest_version() -> str:
    return json.loads(MANIFEST.read_text())["version"]
