"""Support for Open-Meteo Custom weather."""

from __future__ import annotations

from typing import override

from homeassistant.components.weather import (
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import CONF_MODEL, DOMAIN, MODELS
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
    _attr_translation_key = "open_meteo_custom"
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS
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
        self._attribution_translations: dict[str, str] = {}

        model = entry.data.get(CONF_MODEL, "best_match")
        model_label = MODELS.get(model, model)

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Open-Meteo",
            name=f"{entry.title}",
            model=model_label,
        )
        self._update_attribution()

    def _update_attribution(self) -> None:
        """Update attribution string based on translated dictionaries."""
        model = self.coordinator.config_entry.data.get(CONF_MODEL, "best_match")
        if self._attribution_translations and model in self._attribution_translations:
            self._attr_attribution = self._attribution_translations[model]
        elif self._attribution_translations and "fallback" in self._attribution_translations:
            self._attr_attribution = self._attribution_translations["fallback"].format(model=model)
        else:
            # Fallback to English hardcoded value if translations are not loaded
            if model == "best_match":
                self._attr_attribution = "Weather forecast from Open-Meteo (Best Match Auto-Selection)"
            elif model == "dwd_icon_eu":
                self._attr_attribution = "Weather forecast from Deutscher Wetterdienst, delivered by Open-Meteo (ICON Europe)"
            elif model == "dwd_icon":
                self._attr_attribution = "Weather forecast from Deutscher Wetterdienst, delivered by Open-Meteo (ICON Global)"
            elif model == "ecmwf_ifs":
                self._attr_attribution = "Weather forecast from European Centre for Medium-Range Weather Forecasts, delivered by Open-Meteo (ECMWF)"
            elif model == "gfs_global":
                self._attr_attribution = "Weather forecast from National Oceanic and Atmospheric Administration, delivered by Open-Meteo (GFS)"
            elif model == "meteofrance_seamless":
                self._attr_attribution = "Weather forecast from Météo-France, delivered by Open-Meteo (Seamless)"
            elif model == "gem_seamless":
                self._attr_attribution = "Weather forecast from Environment and Climate Change Canada, delivered by Open-Meteo (GEM)"
            elif model == "ukmo_seamless":
                self._attr_attribution = "Weather forecast from UK Met Office, delivered by Open-Meteo (Seamless)"
            else:
                self._attr_attribution = f"Weather forecast from {model}, delivered by Open-Meteo"

    @override
    async def async_added_to_hass(self) -> None:
        """When entity is added to hass."""
        await super().async_added_to_hass()
        from homeassistant.helpers import translation
        
        lang = self.hass.config.language
        translations = await translation.async_get_translations(
            self.hass,
            lang,
            "entity",
            integrations={DOMAIN}
        )
        
        prefix = f"component.{DOMAIN}.entity.weather.open_meteo_custom.state_attributes.attribution."
        for key, val in translations.items():
            if key.startswith(prefix):
                model_key = key[len(prefix):]
                self._attribution_translations[model_key] = val
        
        self._update_attribution()
        self.async_write_ha_state()

    @property
    @override
    def attribution(self) -> str | None:
        """Return the attribution."""
        return self._attr_attribution

    @property
    @override
    def condition(self) -> str | None:
        """Return the current condition."""
        return self.coordinator.data.condition

    @property
    @override
    def native_temperature(self) -> float | None:
        """Return the platform temperature."""
        return self.coordinator.data.temperature

    @property
    @override
    def native_wind_speed(self) -> float | None:
        """Return the wind speed."""
        return self.coordinator.data.wind_speed

    @property
    @override
    def wind_bearing(self) -> float | str | None:
        """Return the wind bearing."""
        return self.coordinator.data.wind_bearing

    @property
    @override
    def humidity(self) -> float | None:
        """Return the humidity."""
        return self.coordinator.data.humidity

    @property
    @override
    def native_pressure(self) -> float | None:
        """Return the pressure."""
        return self.coordinator.data.pressure

    @property
    @override
    def native_apparent_temperature(self) -> float | None:
        """Return the apparent temperature."""
        return self.coordinator.data.apparent_temperature

    @property
    @override
    def native_dew_point(self) -> float | None:
        """Return the dew point."""
        return self.coordinator.data.dew_point

    @property
    @override
    def cloud_coverage(self) -> int | None:
        """Return the cloud coverage."""
        return self.coordinator.data.cloud_coverage

    @property
    @override
    def native_wind_gust_speed(self) -> float | None:
        """Return the wind gust speed."""
        return self.coordinator.data.wind_gust_speed

    @property
    @override
    def native_visibility(self) -> float | None:
        """Return the visibility."""
        if self.coordinator.data.visibility is None:
            return None
        return self.coordinator.data.visibility / 1000

    @property
    @override
    def uv_index(self) -> float | None:
        """Return the UV index."""
        return self.coordinator.data.uv_index

    @callback
    @override
    def _async_forecast_daily(self) -> list[Forecast] | None:
        """Return the daily forecast in native units."""
        return self.coordinator.data.daily_forecast or None

    @callback
    @override
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        """Return the hourly forecast in native units."""
        return self.coordinator.data.hourly_forecast or None

