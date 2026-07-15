"""DataUpdateCoordinator for the Open-Meteo Custom integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import override

from openmeteo_sdk.WeatherApiResponse import WeatherApiResponse
from openmeteo_sdk.Variable import Variable as OMVariable
from openmeteo_sdk.Aggregation import Aggregation as OMAggregation

# Map API string parameter to FlatBuffers Variable identifiers: (variable_id, altitude, aggregation_id)
_API_TO_FB_METADATA = {
    # Current/Hourly
    "weather_code": (OMVariable.weather_code, 0, OMAggregation.none),
    "is_day": (OMVariable.is_day, 0, OMAggregation.none),
    "cloud_cover": (OMVariable.cloud_cover, 0, OMAggregation.none),
    "relative_humidity_2m": (OMVariable.relative_humidity, 2, OMAggregation.none),
    "apparent_temperature": (OMVariable.apparent_temperature, 2, OMAggregation.none),
    "dew_point_2m": (OMVariable.dew_point, 2, OMAggregation.none),
    "precipitation": (OMVariable.precipitation, 0, OMAggregation.none),
    "pressure_msl": (OMVariable.pressure_msl, 0, OMAggregation.none),
    "temperature_2m": (OMVariable.temperature, 2, OMAggregation.none),
    "visibility": (OMVariable.visibility, 0, OMAggregation.none),
    "wind_gusts_10m": (OMVariable.wind_gusts, 10, OMAggregation.none),
    "wind_speed_10m": (OMVariable.wind_speed, 10, OMAggregation.none),
    "precipitation_probability": (OMVariable.precipitation_probability, 0, OMAggregation.none),
    "uv_index": (OMVariable.uv_index, 0, OMAggregation.none),
    "wind_direction_10m": (OMVariable.wind_direction, 10, OMAggregation.none),
    
    # Daily
    "cloud_cover_mean": (OMVariable.cloud_cover, 0, OMAggregation.mean),
    "relative_humidity_2m_mean": (OMVariable.relative_humidity, 2, OMAggregation.mean),
    "apparent_temperature_mean": (OMVariable.apparent_temperature, 2, OMAggregation.mean),
    "dew_point_2m_mean": (OMVariable.dew_point, 2, OMAggregation.mean),
    "precipitation_sum": (OMVariable.precipitation, 0, OMAggregation.sum),
    "pressure_msl_mean": (OMVariable.pressure_msl, 0, OMAggregation.mean),
    "temperature_2m_max": (OMVariable.temperature, 2, OMAggregation.maximum),
    "temperature_2m_min": (OMVariable.temperature, 2, OMAggregation.minimum),
    "wind_gusts_10m_max": (OMVariable.wind_gusts, 10, OMAggregation.maximum),
    "wind_speed_10m_max": (OMVariable.wind_speed, 10, OMAggregation.maximum),
    "precipitation_probability_max": (OMVariable.precipitation_probability, 0, OMAggregation.maximum),
    "uv_index_max": (OMVariable.uv_index, 0, OMAggregation.maximum),
    "wind_direction_10m_dominant": (OMVariable.wind_direction, 10, OMAggregation.dominant),
}


def _find_variable(variables_container, name: str):
    """Find a variable by name in the FlatBuffers variables container."""
    if variables_container is None:
        return None
    meta = _API_TO_FB_METADATA.get(name)
    if not meta:
        return None
    var_id, altitude, aggregation_id = meta
    # Try exact match first
    for i in range(variables_container.VariablesLength()):
        var = variables_container.Variables(i)
        if (var is not None 
            and var.Variable() == var_id 
            and var.Altitude() == altitude 
            and var.Aggregation() == aggregation_id):
            return var
    # Fall back to matching variable and aggregation (ignoring altitude)
    for i in range(variables_container.VariablesLength()):
        var = variables_container.Variables(i)
        if (var is not None 
            and var.Variable() == var_id 
            and var.Aggregation() == aggregation_id):
            return var
    # Fall back to matching just variable (ignoring altitude and aggregation)
    for i in range(variables_container.VariablesLength()):
        var = variables_container.Variables(i)
        if var is not None and var.Variable() == var_id:
            return var
    return None

from homeassistant.components.weather import (
    ATTR_FORECAST_CLOUD_COVERAGE as CLOUD_COVERAGE,
    ATTR_FORECAST_CONDITION as CONDITION,
    ATTR_FORECAST_HUMIDITY as HUMIDITY,
    ATTR_FORECAST_NATIVE_APPARENT_TEMP as NATIVE_APPARENT_TEMP,
    ATTR_FORECAST_NATIVE_DEW_POINT as NATIVE_DEW_POINT,
    ATTR_FORECAST_NATIVE_PRECIPITATION as NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_PRESSURE as NATIVE_PRESSURE,
    ATTR_FORECAST_NATIVE_TEMP as NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW as NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_GUST_SPEED as NATIVE_WIND_GUST_SPEED,
    ATTR_FORECAST_NATIVE_WIND_SPEED as NATIVE_WIND_SPEED,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY as PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_UV_INDEX as UV_INDEX,
    ATTR_FORECAST_WIND_BEARING as WIND_BEARING,
    Forecast,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_LATITUDE, ATTR_LONGITUDE, CONF_ZONE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONF_MODEL,
    CONF_UPDATE_INTERVAL,
    CONF_USE_HA_TIMEZONE,
    DOMAIN,
    FLATBUFFERS_ERROR_MARKER,
    FLATBUFFERS_PREFIX,
    LOGGER,
    OPEN_METEO_URL,
    resolve_condition,
)

type OpenMeteoCustomConfigEntry = ConfigEntry[OpenMeteoCustomDataUpdateCoordinator]

# (api_field_name, data_key, value_converter)
# data_key=None: condition computation only (weather_code / is_day)
_CURRENT_MAP: tuple[tuple[str, str | None, type], ...] = (
    ("weather_code", None, int),
    ("is_day", None, bool),
    ("cloud_cover", "cloud_coverage", int),
    ("relative_humidity_2m", "humidity", float),
    ("apparent_temperature", "apparent_temperature", float),
    ("dew_point_2m", "dew_point", float),
    ("pressure_msl", "pressure", float),
    ("temperature_2m", "temperature", float),
    ("visibility", "visibility", float),
    ("wind_gusts_10m", "wind_gust_speed", float),
    ("wind_speed_10m", "wind_speed", float),
    ("uv_index", "uv_index", float),
    ("wind_direction_10m", "wind_bearing", float),
)

# (api_field_name, forecast_ha_key, value_converter)
# ha_key=None: condition computation only (weather_code / is_day)
_DAILY_MAP: tuple[tuple[str, str | None, type], ...] = (
    ("weather_code", None, int),
    ("cloud_cover_mean", CLOUD_COVERAGE, int),
    ("relative_humidity_2m_mean", HUMIDITY, float),
    ("apparent_temperature_mean", NATIVE_APPARENT_TEMP, float),
    ("dew_point_2m_mean", NATIVE_DEW_POINT, float),
    ("precipitation_sum", NATIVE_PRECIPITATION, float),
    ("pressure_msl_mean", NATIVE_PRESSURE, float),
    ("temperature_2m_max", NATIVE_TEMP, float),
    ("temperature_2m_min", NATIVE_TEMP_LOW, float),
    ("wind_gusts_10m_max", NATIVE_WIND_GUST_SPEED, float),
    ("wind_speed_10m_max", NATIVE_WIND_SPEED, float),
    ("precipitation_probability_max", PRECIPITATION_PROBABILITY, int),
    ("uv_index_max", UV_INDEX, float),
    ("wind_direction_10m_dominant", WIND_BEARING, float),
)

_HOURLY_MAP: tuple[tuple[str, str | None, type], ...] = (
    ("weather_code", None, int),
    ("is_day", None, bool),
    ("cloud_cover", CLOUD_COVERAGE, int),
    ("relative_humidity_2m", HUMIDITY, float),
    ("apparent_temperature", NATIVE_APPARENT_TEMP, float),
    ("dew_point_2m", NATIVE_DEW_POINT, float),
    ("precipitation", NATIVE_PRECIPITATION, float),
    ("pressure_msl", NATIVE_PRESSURE, float),
    ("temperature_2m", NATIVE_TEMP, float),
    ("wind_gusts_10m", NATIVE_WIND_GUST_SPEED, float),
    ("wind_speed_10m", NATIVE_WIND_SPEED, float),
    ("precipitation_probability", PRECIPITATION_PROBABILITY, int),
    ("uv_index", UV_INDEX, float),
    ("wind_direction_10m", WIND_BEARING, float),
)


@dataclass
class OpenMeteoData:
    """Dataclass for Open-Meteo weather data."""

    condition: str | None
    temperature: float | None
    humidity: float | None
    dew_point: float | None
    apparent_temperature: float | None
    cloud_coverage: int | None
    pressure: float | None
    visibility: float | None
    wind_speed: float | None
    wind_bearing: float | None
    wind_gust_speed: float | None
    uv_index: float | None
    daily_forecast: list[Forecast] = field(default_factory=list)
    hourly_forecast: list[Forecast] = field(default_factory=list)


class OpenMeteoCustomDataUpdateCoordinator(DataUpdateCoordinator[OpenMeteoData]):
    """A Open-Meteo Custom Data Update Coordinator."""

    config_entry: OpenMeteoCustomConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: OpenMeteoCustomConfigEntry) -> None:
        """Initialize the Open-Meteo Custom coordinator."""
        update_interval_min = config_entry.data.get(CONF_UPDATE_INTERVAL, 30)
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{config_entry.data[CONF_ZONE]}_{config_entry.data.get(CONF_MODEL, 'best_match')}",
            update_interval=timedelta(minutes=update_interval_min),
        )

    @override
    async def _async_update_data(self) -> OpenMeteoData:
        """Fetch data from Open-Meteo."""
        if (zone := self.hass.states.get(self.config_entry.data[CONF_ZONE])) is None:
            raise UpdateFailed(f"Zone '{self.config_entry.data[CONF_ZONE]}' not found")

        latitude = zone.attributes.get(ATTR_LATITUDE)
        longitude = zone.attributes.get(ATTR_LONGITUDE)
        if latitude is None or longitude is None:
            raise UpdateFailed(f"Zone '{self.config_entry.data[CONF_ZONE]}' is missing latitude or longitude")

        model = self.config_entry.data.get(CONF_MODEL, "best_match")

        use_ha_tz = self.config_entry.data.get(CONF_USE_HA_TIMEZONE, True)
        timezone_param = self.hass.config.time_zone or "auto" if use_ha_tz else "auto"

        params = {
            "latitude": str(latitude),
            "longitude": str(longitude),
            "current": ",".join(f for f, *_ in _CURRENT_MAP),
            "daily": ",".join(f for f, *_ in _DAILY_MAP),
            "hourly": ",".join(f for f, *_ in _HOURLY_MAP),
            "forecast_hours": "168",
            "format": "flatbuffers",
            "precipitation_unit": "mm",
            "temperature_unit": "celsius",
            "timezone": timezone_param,
            "wind_speed_unit": "kmh",
        }

        if model != "best_match":
            params["models"] = model

        try:
            session = async_get_clientsession(self.hass)
            async with session.get(OPEN_METEO_URL, params=params) as http_response:
                http_response.raise_for_status()
                data = await http_response.read()
        except Exception as err:
            raise UpdateFailed(f"Open-Meteo API communication error: {err}") from err

        # Check for JSON error response
        if data.startswith(b"{"):
            try:
                import json
                err_json = json.loads(data)
                reason = err_json.get("reason", "Unknown API error")
                raise UpdateFailed(f"Open-Meteo API error: {reason}")
            except Exception as err:
                if isinstance(err, UpdateFailed):
                    raise
                raise UpdateFailed(f"Open-Meteo API error (failed to parse JSON): {data.decode(errors='replace')}") from err

        # Parse the length-prefixed FlatBuffers frames.
        total = len(data)
        if total < FLATBUFFERS_PREFIX:
            raise UpdateFailed("Malformed response frame header")

        length = int.from_bytes(data[:FLATBUFFERS_PREFIX], byteorder="little")
        if length == FLATBUFFERS_ERROR_MARKER:
            raise UpdateFailed(data[FLATBUFFERS_PREFIX:].decode(errors="replace"))
        if length <= 0:
            raise UpdateFailed("Malformed response frame length")

        frame_end = FLATBUFFERS_PREFIX + length
        if frame_end > total:
            raise UpdateFailed("Malformed response frame length")

        response = WeatherApiResponse.GetRootAs(data, FLATBUFFERS_PREFIX)

        if frame_end < total:
            LOGGER.warning(
                "Received %s extra bytes from Open-Meteo for %s; using first frame only",
                total - frame_end,
                self.config_entry.data[CONF_ZONE],
            )

        offset_sec = response.UtcOffsetSeconds()
        tz = timezone(timedelta(seconds=offset_sec)) if offset_sec is not None else timezone.utc

        # Current weather
        condition: str | None = None
        current_fields: dict[str, float | None] = {
            data_key: None for _, data_key, _ in _CURRENT_MAP if data_key is not None
        }
        if (current := response.Current()) is not None:
            wc_var = _find_variable(current, "weather_code")
            id_var = _find_variable(current, "is_day")
            wc_val = wc_var.Value() if wc_var is not None else 0
            id_val = id_var.Value() if id_var is not None else True
            condition = resolve_condition(int(wc_val), bool(id_val))

            for api_name, data_key, conv in _CURRENT_MAP:
                if data_key is not None:
                    var = _find_variable(current, api_name)
                    if var is not None:
                        current_fields[data_key] = conv(var.Value())

        # Daily forecast
        daily_forecast: list[Forecast] = []
        if (daily := response.Daily()) is not None:
            interval = daily.Interval()
            if interval > 0:
                daily_forecast = [
                    Forecast(datetime=datetime.fromtimestamp(ts, tz=tz).isoformat())
                    for ts in range(daily.Time(), daily.TimeEnd(), interval)
                ]
            wc_var = _find_variable(daily, "weather_code")
            if wc_var is not None:
                for i, entry in enumerate(daily_forecast):
                    if i < wc_var.ValuesLength():
                        entry[CONDITION] = resolve_condition(int(wc_var.Values(i)))
            for api_name, ha_key, conv in _DAILY_MAP:
                if ha_key is not None:
                    var = _find_variable(daily, api_name)
                    if var is not None:
                        for i, entry in enumerate(daily_forecast):
                            if i < var.ValuesLength():
                                entry[ha_key] = conv(var.Values(i))

        # Hourly forecast
        hourly_forecast: list[Forecast] = []
        if (hourly := response.Hourly()) is not None:
            interval = hourly.Interval()
            if interval > 0:
                hourly_forecast = [
                    Forecast(datetime=datetime.fromtimestamp(ts, tz=tz).isoformat())
                    for ts in range(hourly.Time(), hourly.TimeEnd(), interval)
                ]
            wc_var = _find_variable(hourly, "weather_code")
            id_var = _find_variable(hourly, "is_day")
            if wc_var is not None and id_var is not None:
                for i, entry in enumerate(hourly_forecast):
                    if i < wc_var.ValuesLength() and i < id_var.ValuesLength():
                        entry[CONDITION] = resolve_condition(
                            int(wc_var.Values(i)), bool(id_var.Values(i))
                        )
            elif wc_var is not None:
                for i, entry in enumerate(hourly_forecast):
                    if i < wc_var.ValuesLength():
                        entry[CONDITION] = resolve_condition(int(wc_var.Values(i)))

            for api_name, ha_key, conv in _HOURLY_MAP:
                if ha_key is not None:
                    var = _find_variable(hourly, api_name)
                    if var is not None:
                        for i, entry in enumerate(hourly_forecast):
                            if i < var.ValuesLength():
                                entry[ha_key] = conv(var.Values(i))

        return OpenMeteoData(
            condition=condition,
            **current_fields,
            daily_forecast=daily_forecast,
            hourly_forecast=hourly_forecast,
        )


