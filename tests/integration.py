from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.aoe2.api import ClientName
from custom_components.aoe2.const import CONF_CLIENT, CONF_PROFILE_ID, DEFAULT_CLIENT, DOMAIN

PROFILE_ID = 1


def config_entry_for(client_name: ClientName = DEFAULT_CLIENT) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=str(PROFILE_ID),
        data={CONF_CLIENT: client_name, CONF_PROFILE_ID: PROFILE_ID},
    )


async def set_up(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def set_up_integration(hass: HomeAssistant) -> MockConfigEntry:
    entry = config_entry_for()
    await set_up(hass, entry)
    return entry


async def refresh(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    await entry.runtime_data.async_refresh()
    await hass.async_block_till_done()


def entity_id_for(hass: HomeAssistant, platform: Platform, unique_key: str) -> str:
    unique_id = f"{PROFILE_ID}_{unique_key}"
    entity_id = entity_registry.async_get(hass).async_get_entity_id(platform, DOMAIN, unique_id)
    assert entity_id is not None, f"No {platform} entity with unique ID {unique_id}"
    return entity_id


def state_of(hass: HomeAssistant, platform: Platform, unique_key: str) -> State:
    state = hass.states.get(entity_id_for(hass, platform, unique_key))
    assert state is not None
    return state
