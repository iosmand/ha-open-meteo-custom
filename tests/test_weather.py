import pytest
from homeassistant.core import HomeAssistant
from homeassistant.components.weather import (
    ATTR_WEATHER_APPARENT_TEMPERATURE,
    ATTR_WEATHER_CLOUD_COVERAGE,
    ATTR_WEATHER_DEW_POINT,
    ATTR_WEATHER_HUMIDITY,
    ATTR_WEATHER_PRESSURE,
    ATTR_WEATHER_TEMPERATURE,
    ATTR_WEATHER_UV_INDEX,
    ATTR_WEATHER_VISIBILITY,
    ATTR_WEATHER_WIND_BEARING,
    ATTR_WEATHER_WIND_GUST_SPEED,
    ATTR_WEATHER_WIND_SPEED,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_NATIVE_TEMP,
    DOMAIN as WEATHER_DOMAIN,
)
from homeassistant.const import STATE_UNAVAILABLE
from custom_components.open_meteo_custom.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

async def test_weather_entity_properties(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_zone: None,
    mock_get_clientsession,
) -> None:
    """Test weather entity state and attributes are populated from FlatBuffers."""
    mock_config_entry.add_to_hass(hass)
    
    # Set up the integration entry
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_ids = hass.states.async_entity_ids(WEATHER_DOMAIN)
    assert len(entity_ids) == 1
    entity_id = entity_ids[0]

    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state != STATE_UNAVAILABLE

    # Verify native properties mapping from FlatBuffers
    attributes = state.attributes
    assert attributes[ATTR_WEATHER_TEMPERATURE] == pytest.approx(28.35, abs=0.1)
    assert attributes[ATTR_WEATHER_APPARENT_TEMPERATURE] == pytest.approx(27.26, abs=0.1)
    assert attributes[ATTR_WEATHER_DEW_POINT] == pytest.approx(10.08, abs=0.1)
    assert attributes[ATTR_WEATHER_HUMIDITY] == 32
    assert attributes[ATTR_WEATHER_PRESSURE] == pytest.approx(1011.9, abs=0.1)
    assert attributes[ATTR_WEATHER_VISIBILITY] == pytest.approx(46.4, abs=0.1)  # 46400 m / 1000 = 46.4 km
    assert attributes[ATTR_WEATHER_WIND_SPEED] == pytest.approx(7.69, abs=0.1)
    assert attributes[ATTR_WEATHER_WIND_GUST_SPEED] == pytest.approx(22.68, abs=0.1)
    assert attributes[ATTR_WEATHER_WIND_BEARING] == pytest.approx(10.78, abs=0.1)
    assert attributes[ATTR_WEATHER_UV_INDEX] == pytest.approx(0.0, abs=0.1)
    assert attributes[ATTR_WEATHER_CLOUD_COVERAGE] == 0

async def test_weather_forecast(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_zone: None,
    mock_get_clientsession,
) -> None:
    """Test weather forecast methods return daily and hourly forecasts."""
    mock_config_entry.add_to_hass(hass)
    
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Get the entity from registry or instantiate it
    from custom_components.open_meteo_custom.weather import OpenMeteoCustomWeatherEntity
    coordinator = mock_config_entry.runtime_data
    weather_entity = OpenMeteoCustomWeatherEntity(entry=mock_config_entry, coordinator=coordinator)
    weather_entity.hass = hass

    # Test daily forecast method
    daily_forecasts = weather_entity._async_forecast_daily()
    assert daily_forecasts is not None
    assert len(daily_forecasts) == 7
    first_day = daily_forecasts[0]
    assert first_day[ATTR_FORECAST_CONDITION] == "sunny"
    assert first_day[ATTR_FORECAST_NATIVE_TEMP] == pytest.approx(34.7, abs=0.1)

    # Test hourly forecast method
    hourly_forecasts = weather_entity._async_forecast_hourly()
    assert hourly_forecasts is not None
    assert len(hourly_forecasts) == 168
    first_hour = hourly_forecasts[0]
    assert first_hour[ATTR_FORECAST_CONDITION] == "clear-night"
    assert first_hour[ATTR_FORECAST_NATIVE_TEMP] == pytest.approx(23.7, abs=0.1)
