import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant
from custom_components.open_meteo_custom.const import DOMAIN, CONF_MODEL, CONF_UPDATE_INTERVAL, CONF_USE_HA_TIMEZONE
from homeassistant.const import CONF_ZONE
from pytest_homeassistant_custom_component.common import MockConfigEntry

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for testing."""
    yield

@pytest.fixture
def openmeteo_fixture_data() -> bytes:
    """Load mock binary FlatBuffers response."""
    with open("tests/fixtures/openmeteo_response.bin", "rb") as f:
        return f.read()

@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Mock a config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Home (Best Match (Auto))",
        data={
            CONF_ZONE: "zone.home",
            CONF_MODEL: "best_match",
            CONF_UPDATE_INTERVAL: 30,
            CONF_USE_HA_TIMEZONE: True,
        },
        entry_id="open_meteo_custom_test_entry",
    )

@pytest.fixture
def mock_zone(hass: HomeAssistant) -> None:
    """Mock a zone entity with latitude and longitude."""
    hass.states.async_set(
        "zone.home",
        "zoning",
        {
            ATTR_LATITUDE: 38.5163,
            ATTR_LONGITUDE: 27.0475,
            "friendly_name": "Home",
        }
    )

@pytest.fixture
def mock_get_clientsession(openmeteo_fixture_data):
    """Fixture to mock client session for open_meteo_custom coordinator."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.read = AsyncMock(return_value=openmeteo_fixture_data)
    
    with patch("custom_components.open_meteo_custom.coordinator.async_get_clientsession") as mock_session_get:
        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_resp
        mock_session_get.return_value = mock_session
        yield mock_session_get
