import pytest
from homeassistant.core import HomeAssistant
from custom_components.open_meteo_custom.diagnostics import async_get_config_entry_diagnostics
from pytest_homeassistant_custom_component.common import MockConfigEntry

async def test_diagnostics(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_zone: None,
    mock_get_clientsession,
) -> None:
    """Test diagnostics output redacts sensitive coordinate information."""
    mock_config_entry.add_to_hass(hass)
    
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Get diagnostics
    diag = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    
    assert diag is not None
    assert "config_entry" in diag
    assert "coordinator_data" in diag
    
    # Check that latitude/longitude is redacted or not present in coordinator_data
    coord_data = diag["coordinator_data"]
    assert coord_data is not None
    
    # Redacted values should be replaced or hidden
    assert "latitude" not in coord_data or coord_data["latitude"] == "**REDACTED**"
    assert "longitude" not in coord_data or coord_data["longitude"] == "**REDACTED**"
