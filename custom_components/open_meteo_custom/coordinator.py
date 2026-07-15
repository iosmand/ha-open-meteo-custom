"""DataUpdateCoordinator for the Open-Meteo Custom integration."""

import json
from typing import override
from yarl import URL

from open_meteo import (
    Forecast,
    OpenMeteo,
    OpenMeteoError,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ZONE, EntityStateAttribute
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import CONF_MODEL, DOMAIN, LOGGER, SCAN_INTERVAL

type OpenMeteoCustomConfigEntry = ConfigEntry[OpenMeteoCustomDataUpdateCoordinator]


class OpenMeteoCustomDataUpdateCoordinator(DataUpdateCoordinator[Forecast]):
    """A Open-Meteo Custom Data Update Coordinator."""

    config_entry: OpenMeteoCustomConfigEntry

    def __init__(self, hass: HomeAssistant, config_entry: OpenMeteoCustomConfigEntry) -> None:
        """Initialize the Open-Meteo Custom coordinator."""
        super().__init__(
            hass,
            LOGGER,
            config_entry=config_entry,
            name=f"{DOMAIN}_{config_entry.data[CONF_ZONE]}_{config_entry.data.get(CONF_MODEL, 'best_match')}",
            update_interval=SCAN_INTERVAL,
        )
        session = async_get_clientsession(hass)
        self.open_meteo = OpenMeteo(session=session)

    @override
    async def _async_update_data(self) -> Forecast:
        """Fetch data from Open-Meteo."""
        if (zone := self.hass.states.get(self.config_entry.data[CONF_ZONE])) is None:
            raise UpdateFailed(f"Zone '{self.config_entry.data[CONF_ZONE]}' not found")

        latitude = zone.attributes[EntityStateAttribute.LATITUDE]
        longitude = zone.attributes[EntityStateAttribute.LONGITUDE]
        model = self.config_entry.data.get(CONF_MODEL, "best_match")

        query_params = {
            "latitude": str(latitude),
            "longitude": str(longitude),
            "current_weather": "true",
            "hourly": ",".join([
                "relativehumidity_2m",
                "apparent_temperature",
                "pressure_msl",
                "dewpoint_2m",
                "windgusts_10m",
                "cloudcover",
                "temperature_2m",
                "weathercode",
                "precipitation",
            ]),
            "daily": ",".join([
                "weathercode",
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "winddirection_10m_dominant",
                "windspeed_10m_max",
            ]),
            "precipitation_unit": "mm",
            "temperature_unit": "celsius",
            "timezone": "UTC",
            "windspeed_unit": "kmh",
        }

        if model != "best_match":
            query_params["models"] = model

        url = URL("https://api.open-meteo.com/v1/forecast").with_query(query_params)
        LOGGER.debug("Fetching Open-Meteo forecast URL: %s", url)

        try:
            raw_data = await self.open_meteo._request(url=url)
            data_dict = json.loads(raw_data)
            cleaned_dict = clean_forecast_data(data_dict)
            return Forecast.from_dict(cleaned_dict)
        except OpenMeteoError as err:
            raise UpdateFailed(f"Open-Meteo API communication error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error updating Open-Meteo data: {err}") from err

    @property
    def current_hourly_index(self) -> int | None:
        """Find the index in the hourly data corresponding to the current time."""
        if not self.data or not self.data.hourly or not self.data.hourly.time:
            return None

        now = dt_util.utcnow()
        closest_index = None
        min_diff = None

        for index, timestamp in enumerate(self.data.hourly.time):
            if timestamp.tzinfo is None:
                timestamp = timestamp.replace(tzinfo=dt_util.UTC)

            diff = abs((timestamp - now).total_seconds())
            if min_diff is None or diff < min_diff:
                min_diff = diff
                closest_index = index

        return closest_index


def clean_forecast_data(data_dict: dict) -> dict:
    """Clean the forecast data dictionary to prevent Mashumaro deserialization errors.

    Regional models return null (None) values at the end of their forecast lists
    for days beyond their forecast horizon. This function truncates these lists
    to the maximum length of continuous non-null data.
    """
    # Clean hourly data
    if "hourly" in data_dict and isinstance(data_dict["hourly"], dict):
        hourly = data_dict["hourly"]
        if "time" in hourly and isinstance(hourly["time"], list):
            original_len = len(hourly["time"])
            max_len = original_len
            check_keys = ["temperature_2m", "weathercode", "relativehumidity_2m"]
            for key in check_keys:
                if key in hourly and isinstance(hourly[key], list):
                    for idx, val in enumerate(hourly[key]):
                        if val is None:
                            max_len = min(max_len, idx)
                            break
            if max_len < original_len:
                LOGGER.debug("Hourly forecast truncated from %d to %d elements due to null values", original_len, max_len)
            for key, val_list in hourly.items():
                if isinstance(val_list, list):
                    hourly[key] = val_list[:max_len]

    # Clean daily data
    if "daily" in data_dict and isinstance(data_dict["daily"], dict):
        daily = data_dict["daily"]
        if "time" in daily and isinstance(daily["time"], list):
            original_len = len(daily["time"])
            max_len = original_len
            check_keys = ["temperature_2m_max", "weathercode"]
            for key in check_keys:
                if key in daily and isinstance(daily[key], list):
                    for idx, val in enumerate(daily[key]):
                        if val is None:
                            max_len = min(max_len, idx)
                            break
            if max_len < original_len:
                LOGGER.debug("Daily forecast truncated from %d to %d elements due to null values", original_len, max_len)
            for key, val_list in daily.items():
                if isinstance(val_list, list):
                    daily[key] = val_list[:max_len]

    return data_dict

