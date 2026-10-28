import subprocess
import sys
from pathlib import Path

import pytest

INTEGRATION = Path(__file__).parents[1] / "custom_components" / "aoe2"
INTEGRATION_PACKAGE = "custom_components.aoe2"

HOME_ASSISTANT_FREE_PACKAGES = ["api", "logic"]

ALLOWED_IMPORTS = {
    "api": {"api"},
    "logic": {"api", "logic"},
    "ha_internals": {"api", "logic", "const", "ha_internals"},
}

IMPORT_WITHOUT_INTEGRATION_SETUP = """
import importlib, pkgutil, sys, types

integration = types.ModuleType({integration_package!r})
integration.__path__ = [{integration_path!r}]
sys.modules[{integration_package!r}] = integration

package = importlib.import_module({package!r})
for module in pkgutil.walk_packages(package.__path__, f"{{package.__name__}}."):
    importlib.import_module(module.name)

print("\\n".join(sys.modules))
"""


def get_modules_loaded_by(package: str) -> list[str]:
    """The integration's own __init__ imports Home Assistant, so it is stubbed out."""
    script = IMPORT_WITHOUT_INTEGRATION_SETUP.format(
        integration_package=INTEGRATION_PACKAGE,
        integration_path=str(INTEGRATION),
        package=f"{INTEGRATION_PACKAGE}.{package}",
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=True,
        cwd=INTEGRATION.parents[1],
    )
    return result.stdout.split()


def get_home_assistant_modules(modules: list[str]) -> list[str]:
    return [module for module in modules if module.split(".")[0] == "homeassistant"]


def get_integration_parts(modules: list[str]) -> set[str]:
    prefix = f"{INTEGRATION_PACKAGE}."
    return {
        module.removeprefix(prefix).split(".")[0] for module in modules if module.startswith(prefix)
    }


@pytest.mark.parametrize("package", HOME_ASSISTANT_FREE_PACKAGES)
def test_package_does_not_import_home_assistant(package: str):
    # When
    loaded = get_modules_loaded_by(package)

    # Then
    assert get_home_assistant_modules(loaded) == []


@pytest.mark.parametrize(("package", "allowed"), ALLOWED_IMPORTS.items())
def test_package_only_imports_allowed_parts_of_the_integration(package: str, allowed: set[str]):
    # When
    loaded = get_modules_loaded_by(package)

    # Then
    assert get_integration_parts(loaded) <= allowed
