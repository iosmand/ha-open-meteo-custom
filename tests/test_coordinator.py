import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from custom_components.open_meteo_custom.coordinator import OpenMeteoCustomDataUpdateCoordinator
from custom_components.open_meteo_custom.const import FLATBUFFERS_ERROR_MARKER
from pytest_homeassistant_custom_component.common import MockConfigEntry

async def test_coordinator_missing_zone(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test coordinator update fails if the zone is not found in Home Assistant."""
    coordinator = OpenMeteoCustomDataUpdateCoordinator(hass, mock_config_entry)
    with pytest.raises(UpdateFailed, match="Zone 'zone.home' not found"):
        await coordinator._async_update_data()

async def test_coordinator_missing_coordinates(hass: HomeAssistant, mock_config_entry: MockConfigEntry) -> None:
    """Test coordinator update fails if the zone lacks coordinates."""
    # Set zone without latitude and longitude
    hass.states.async_set("zone.home", "zoning", {"friendly_name": "Home"})
    
    coordinator = OpenMeteoCustomDataUpdateCoordinator(hass, mock_config_entry)
    with pytest.raises(UpdateFailed, match="Zone 'zone.home' is missing latitude or longitude"):
        await coordinator._async_update_data()

async def test_coordinator_communication_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_zone: None
) -> None:
    """Test coordinator handles communication errors gracefully."""
    coordinator = OpenMeteoCustomDataUpdateCoordinator(hass, mock_config_entry)

    with patch("custom_components.open_meteo_custom.coordinator.async_get_clientsession") as mock_session_get:
        mock_session = MagicMock()
        mock_session.get.side_effect = Exception("Connection closed")
        mock_session_get.return_value = mock_session

        with pytest.raises(UpdateFailed, match="Open-Meteo API communication error: Connection closed"):
            await coordinator._async_update_data()

async def test_coordinator_malformed_header(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_zone: None
) -> None:
    """Test coordinator handles responses shorter than 4 bytes."""
    coordinator = OpenMeteoCustomDataUpdateCoordinator(hass, mock_config_entry)

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.read = AsyncMock(return_value=b"abc")

    with patch("custom_components.open_meteo_custom.coordinator.async_get_clientsession") as mock_session_get:
        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_resp
        mock_session_get.return_value = mock_session

        with pytest.raises(UpdateFailed, match="Malformed response frame header"):
            await coordinator._async_update_data()

async def test_coordinator_error_marker(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_zone: None
) -> None:
    """Test coordinator handles error responses starting with the error marker."""
    coordinator = OpenMeteoCustomDataUpdateCoordinator(hass, mock_config_entry)

    marker = FLATBUFFERS_ERROR_MARKER.to_bytes(4, byteorder="little")
    error_msg = b"API error reason message"
    payload = marker + error_msg

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.read = AsyncMock(return_value=payload)

    with patch("custom_components.open_meteo_custom.coordinator.async_get_clientsession") as mock_session_get:
        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_resp
        mock_session_get.return_value = mock_session

        with pytest.raises(UpdateFailed, match="API error reason message"):
            await coordinator._async_update_data()

async def test_coordinator_json_error(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_zone: None
) -> None:
    """Test coordinator parses JSON error responses correctly."""
    coordinator = OpenMeteoCustomDataUpdateCoordinator(hass, mock_config_entry)

    payload = b'{"error": true, "reason": "Invalid parameter model"}'

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.read = AsyncMock(return_value=payload)

    with patch("custom_components.open_meteo_custom.coordinator.async_get_clientsession") as mock_session_get:
        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_resp
        mock_session_get.return_value = mock_session

        with pytest.raises(UpdateFailed, match="Open-Meteo API error: Invalid parameter model"):
            await coordinator._async_update_data()

async def test_coordinator_successful_parse(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_zone: None, openmeteo_fixture_data: bytes
) -> None:
    """Test coordinator parses valid FlatBuffers data successfully."""
    coordinator = OpenMeteoCustomDataUpdateCoordinator(hass, mock_config_entry)

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.read = AsyncMock(return_value=openmeteo_fixture_data)

    with patch("custom_components.open_meteo_custom.coordinator.async_get_clientsession") as mock_session_get:
        mock_session = MagicMock()
        mock_session.get.return_value.__aenter__.return_value = mock_resp
        mock_session_get.return_value = mock_session

        data = await coordinator._async_update_data()

    assert data.condition is not None
    assert data.temperature is not None
    assert data.humidity is not None
    assert data.pressure is not None
    assert data.apparent_temperature is not None
    assert data.dew_point is not None
    assert data.cloud_coverage is not None
    assert data.wind_gust_speed is not None
    assert data.wind_speed is not None
    assert data.wind_bearing is not None
    assert data.uv_index is not None
    assert len(data.daily_forecast) > 0
    assert len(data.hourly_forecast) > 0
