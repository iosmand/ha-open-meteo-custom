"""Support for Open-Meteo Custom weather."""

from datetime import datetime, time
from typing import override

from homeassistant.components.weather import (
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_WIND_BEARING,
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import UnitOfPrecipitationDepth, UnitOfSpeed, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .const import ATTR_CONDITION_CLEAR_NIGHT, ATTR_CONDITION_SUNNY, CONF_MODEL, DOMAIN, MODELS, WMO_TO_HA_CONDITION_MAP
from .coordinator import OpenMeteoCustomConfigEntry, OpenMeteoCustomDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OpenMeteoCustomConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Open-Meteo Custom weather entity based on a config entry."""
    coordinator = entry.runtime_data
    async_add_entities([OpenMeteoCustomWeatherEntity(entry=entry, coordinator=coordinator)])


class OpenMeteoCustomWeatherEntity(
    SingleCoordinatorWeatherEntity[OpenMeteoCustomDataUpdateCoordinator]
):
    """Defines an Open-Meteo Custom weather entity."""

    _attr_has_entity_name = True
    _attr_name = None
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(
        self,
        *,
        entry: OpenMeteoCustomConfigEntry,
        coordinator: OpenMeteoCustomDataUpdateCoordinator,
    ) -> None:
        """Initialize Open-Meteo Custom weather entity."""
        super().__init__(coordinator=coordinator)
        self._attr_unique_id = f"{entry.entry_id}_weather"

        model = entry.data.get(CONF_MODEL, "best_match")
        model_label = MODELS.get(model, model)

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Open-Meteo",
            name=f"{entry.title}",
            model=model_label,
        )

    def _get_current_hourly_index(self) -> int | None:
        """Find the index in the hourly data corresponding to the current time."""
        if not self.coordinator.data or not self.coordinator.data.hourly or not self.coordinator.data.hourly.time:
            return None
        
        now = dt_util.utcnow()
        closest_index = None
        min_diff = None
        
        for index, timestamp in enumerate(self.coordinator.data.hourly.time):
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=dt_util.UTC)
            
            diff = abs((timestamp - now).total_seconds())
            if min_diff is None or diff < min_diff:
                min_diff = diff
                closest_index = index
                
        return closest_index

    @property
    @override
    def condition(self) -> str | None:
        """Return the current condition."""
        if not self.coordinator.data.current_weather:
            return None
        weather_code = self.coordinator.data.current_weather.weather_code
        is_day = self.coordinator.is_day
        cond = WMO_TO_HA_CONDITION_MAP.get(weather_code)
        if cond == ATTR_CONDITION_SUNNY and not is_day:
            return ATTR_CONDITION_CLEAR_NIGHT
        return cond

    @property
    @override
    def native_temperature(self) -> float | None:
        """Return the platform temperature."""
        if not self.coordinator.data.current_weather:
            return None
        return self.coordinator.data.current_weather.temperature

    @property
    @override
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        if not self.coordinator.data.current_weather:
            return None
        return self.coordinator.data.current_weather.wind_speed

    @property
    @override
    def wind_bearing(self) -> float | str | None:
        """Return the wind bearing."""
        if not self.coordinator.data.current_weather:
            return None
        return self.coordinator.data.current_weather.wind_direction

    @property
    @override
    def humidity(self) -> float | None:
        """Return the humidity."""
        idx = self._get_current_hourly_index()
        if idx is None or self.coordinator.data.hourly is None or self.coordinator.data.hourly.relative_humidity_2m is None:
            return None
        if idx >= len(self.coordinator.data.hourly.relative_humidity_2m):
            return None
        return self.coordinator.data.hourly.relative_humidity_2m[idx]

    @property
    @override
    def native_pressure(self) -> float | None:
        """Return the pressure."""
        idx = self._get_current_hourly_index()
        if idx is None or self.coordinator.data.hourly is None or self.coordinator.data.hourly.pressure_msl is None:
            return None
        if idx >= len(self.coordinator.data.hourly.pressure_msl):
            return None
        return self.coordinator.data.hourly.pressure_msl[idx]

    @property
    @override
    def native_apparent_temperature(self) -> float | None:
        """Return the apparent temperature."""
        idx = self._get_current_hourly_index()
        if idx is None or self.coordinator.data.hourly is None or self.coordinator.data.hourly.apparent_temperature is None:
            return None
        if idx >= len(self.coordinator.data.hourly.apparent_temperature):
            return None
        return self.coordinator.data.hourly.apparent_temperature[idx]

    @property
    @override
    def native_dew_point(self) -> float | None:
        """Return the dew point."""
        idx = self._get_current_hourly_index()
        if idx is None or self.coordinator.data.hourly is None or self.coordinator.data.hourly.dew_point_2m is None:
            return None
        if idx >= len(self.coordinator.data.hourly.dew_point_2m):
            return None
        return self.coordinator.data.hourly.dew_point_2m[idx]

    @property
    @override
    def cloud_coverage(self) -> int | None:
        """Return the cloud coverage."""
        idx = self._get_current_hourly_index()
        if idx is None or self.coordinator.data.hourly is None or self.coordinator.data.hourly.cloud_cover is None:
            return None
        if idx >= len(self.coordinator.data.hourly.cloud_cover):
            return None
        return self.coordinator.data.hourly.cloud_cover[idx]

    @property
    @override
    def native_wind_gust_speed(self) -> float | None:
        """Return the wind gust speed."""
        idx = self._get_current_hourly_index()
        if idx is None or self.coordinator.data.hourly is None or self.coordinator.data.hourly.wind_gusts_10m is None:
            return None
        if idx >= len(self.coordinator.data.hourly.wind_gusts_10m):
            return None
        return self.coordinator.data.hourly.wind_gusts_10m[idx]

    @callback
    @override
    def _async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        if self.coordinator.data.daily is None:
            return None

        forecasts: list[Forecast] = []
        daily = self.coordinator.data.daily

        for index, date in enumerate(daily.time):
            _datetime = datetime.combine(date=date, time=time(0), tzinfo=dt_util.UTC)
            forecast = Forecast(
                datetime=_datetime.isoformat(),
            )

            if daily.weathercode is not None:
                forecast["condition"] = WMO_TO_HA_CONDITION_MAP.get(
                    daily.weathercode[index]
                )

            if daily.precipitation_sum is not None:
                forecast["native_precipitation"] = daily.precipitation_sum[index]

            if daily.temperature_2m_max is not None:
                forecast["native_temperature"] = daily.temperature_2m_max[index]

            if daily.temperature_2m_min is not None:
                forecast["native_temp_low"] = daily.temperature_2m_min[index]

            if daily.wind_direction_10m_dominant is not None:
                forecast["wind_bearing"] = daily.wind_direction_10m_dominant[index]

            if daily.wind_speed_10m_max is not None:
                forecast["native_wind_speed"] = daily.wind_speed_10m_max[index]

            forecasts.append(forecast)

        return forecasts

    @callback
    @override
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast in native units."""
        if self.coordinator.data.hourly is None:
            return None

        forecasts: list[Forecast] = []
        today = dt_util.utcnow()
        hourly = self.coordinator.data.hourly

        for index, _datetime in enumerate(hourly.time):
            if _datetime.tzinfo is None:
                _datetime = _datetime.replace(tzinfo=dt_util.UTC)
            if _datetime < today:
                continue

            forecast = Forecast(
                datetime=_datetime.isoformat(),
            )

            if hourly.weather_code is not None:
                cond = WMO_TO_HA_CONDITION_MAP.get(hourly.weather_code[index])
                is_day = self.coordinator.hourly_is_day[index] if (self.coordinator.hourly_is_day and index < len(self.coordinator.hourly_is_day)) else 1
                if cond == ATTR_CONDITION_SUNNY and not is_day:
                    cond = ATTR_CONDITION_CLEAR_NIGHT
                forecast["condition"] = cond

            if hourly.precipitation is not None:
                forecast["native_precipitation"] = hourly.precipitation[index]

            if hourly.temperature_2m is not None:
                forecast["native_temperature"] = hourly.temperature_2m[index]

            if hourly.relative_humidity_2m is not None:
                forecast["humidity"] = hourly.relative_humidity_2m[index]

            if hourly.apparent_temperature is not None:
                forecast["native_apparent_temperature"] = hourly.apparent_temperature[index]

            if hourly.pressure_msl is not None:
                forecast["native_pressure"] = hourly.pressure_msl[index]

            if hourly.dew_point_2m is not None:
                forecast["native_dew_point"] = hourly.dew_point_2m[index]

            if hourly.wind_gusts_10m is not None:
                forecast["native_wind_gust_speed"] = hourly.wind_gusts_10m[index]

            if hourly.cloud_cover is not None:
                forecast["cloud_coverage"] = hourly.cloud_cover[index]

            forecasts.append(forecast)

        return forecasts
