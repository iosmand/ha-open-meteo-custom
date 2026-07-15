import pytest
from homeassistant.core import HomeAssistant
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import STATE_UNAVAILABLE
from custom_components.open_meteo_custom.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

async def test_sensor_entities(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_zone: None,
    mock_get_clientsession,
) -> None:
    """Test sensor entities state values and configuration attributes."""
    mock_config_entry.add_to_hass(hass)

    # Set up the integration entry
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Verify sensor states are correctly set from FlatBuffers data
    temp_state = hass.states.get("sensor.home_best_match_auto_temperature")
    assert temp_state is not None
    assert float(temp_state.state) == pytest.approx(28.35, abs=0.1)
    assert temp_state.attributes["unit_of_measurement"] == "°C"

    humidity_state = hass.states.get("sensor.home_best_match_auto_humidity")
    assert humidity_state is not None
    assert humidity_state.state == "32.0"
    assert humidity_state.attributes["unit_of_measurement"] == "%"

    pressure_state = hass.states.get("sensor.home_best_match_auto_pressure")
    assert pressure_state is not None
    assert float(pressure_state.state) == pytest.approx(1011.9, abs=0.1)
    assert pressure_state.attributes["unit_of_measurement"] == "hPa"

    apparent_temp_state = hass.states.get("sensor.home_best_match_auto_apparent_temperature")
    assert apparent_temp_state is not None
    assert float(apparent_temp_state.state) == pytest.approx(27.26, abs=0.1)
    assert apparent_temp_state.attributes["unit_of_measurement"] == "°C"

    dew_point_state = hass.states.get("sensor.home_best_match_auto_dew_point")
    assert dew_point_state is not None
    assert float(dew_point_state.state) == pytest.approx(10.08, abs=0.1)
    assert dew_point_state.attributes["unit_of_measurement"] == "°C"

    cloud_cover_state = hass.states.get("sensor.home_best_match_auto_cloud_cover")
    assert cloud_cover_state is not None
    assert cloud_cover_state.state == "0"
    assert cloud_cover_state.attributes["unit_of_measurement"] == "%"

    wind_gust_state = hass.states.get("sensor.home_best_match_auto_wind_gust")
    assert wind_gust_state is not None
    assert float(wind_gust_state.state) == pytest.approx(22.68, abs=0.1)
    assert wind_gust_state.attributes["unit_of_measurement"] == "km/h"

    wind_speed_state = hass.states.get("sensor.home_best_match_auto_wind_speed")
    assert wind_speed_state is not None
    assert float(wind_speed_state.state) == pytest.approx(7.69, abs=0.1)
    assert wind_speed_state.attributes["unit_of_measurement"] == "km/h"

    visibility_state = hass.states.get("sensor.home_best_match_auto_visibility")
    assert visibility_state is not None
    assert float(visibility_state.state) == pytest.approx(46.4, abs=0.1)
    assert visibility_state.attributes["unit_of_measurement"] == "km"
