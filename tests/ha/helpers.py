from pathlib import Path

from pydantic import BaseModel

MANIFEST = Path(__file__).parents[2] / "custom_components/aoe2/manifest.json"


class Manifest(BaseModel):
    version: str


def read_manifest_version() -> str:
    return Manifest.model_validate_json(MANIFEST.read_text()).version
