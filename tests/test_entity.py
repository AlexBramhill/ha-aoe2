import pytest
from homeassistant.const import ATTR_ATTRIBUTION, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry

from custom_components.aoe2.const import DOMAIN
from tests.fake_client import FakeAoeClient
from tests.integration import PROFILE_ID, set_up_integration, state_of


@pytest.mark.usefixtures("created_client_names")
async def test_entities_credit_the_configured_data_source(
    hass: HomeAssistant, fake_client: FakeAoeClient
):
    # When
    await set_up_integration(hass)

    # Then
    rating = state_of(hass, Platform.SENSOR, "rm_1v1_rating")
    assert rating.attributes[ATTR_ATTRIBUTION] == fake_client.attribution


@pytest.mark.usefixtures("created_client_names")
async def test_device_links_to_profile_on_the_configured_data_source(
    hass: HomeAssistant, fake_client: FakeAoeClient
):
    # When
    entry = await set_up_integration(hass)

    # Then
    device = device_registry.async_get(hass).async_get_device_by_identifier(
        (DOMAIN, str(PROFILE_ID)), entry.entry_id
    )
    assert device is not None
    assert device.configuration_url == fake_client.profile_url(PROFILE_ID)
    assert device.name == fake_client.profile.name
