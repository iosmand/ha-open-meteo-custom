"""Support for Open-Meteo Custom sensors."""

from dataclasses import dataclass
from collections.abc import Callable
from typing import Final

from open_meteo import Forecast

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_MODEL, DOMAIN, MODELS
from .coordinator import OpenMeteoCustomConfigEntry, OpenMeteoCustomDataUpdateCoordinator


@dataclass(frozen=True, kw_only=True)
class OpenMeteoCustomSensorEntityDescription(SensorEntityDescription):
    """Describes Open-Meteo Custom sensor entity."""

    value_fn: Callable[[Forecast, int], float | int | None]


SENSOR_DESCRIPTIONS: Final[tuple[OpenMeteoCustomSensorEntityDescription, ...]] = (
    OpenMeteoCustomSensorEntityDescription(
        key="humidity",
        name="Humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, idx: data.hourly.relative_humidity_2m[idx]
        if data.hourly and data.hourly.relative_humidity_2m and idx < len(data.hourly.relative_humidity_2m)
        else None,
    ),
    OpenMeteoCustomSensorEntityDescription(
        key="pressure",
        name="Pressure",
        translation_key="pressure",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.HPA,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, idx: data.hourly.pressure_msl[idx]
        if data.hourly and data.hourly.pressure_msl and idx < len(data.hourly.pressure_msl)
        else None,
    ),
    OpenMeteoCustomSensorEntityDescription(
        key="apparent_temperature",
        name="Apparent Temperature",
        translation_key="apparent_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, idx: data.hourly.apparent_temperature[idx]
        if data.hourly and data.hourly.apparent_temperature and idx < len(data.hourly.apparent_temperature)
        else None,
    ),
    OpenMeteoCustomSensorEntityDescription(
        key="dew_point",
        name="Dew Point",
        translation_key="dew_point",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, idx: data.hourly.dew_point_2m[idx]
        if data.hourly and data.hourly.dew_point_2m and idx < len(data.hourly.dew_point_2m)
        else None,
    ),
    OpenMeteoCustomSensorEntityDescription(
        key="cloud_cover",
        name="Cloud Cover",
        translation_key="cloud_cover",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, idx: data.hourly.cloud_cover[idx]
        if data.hourly and data.hourly.cloud_cover and idx < len(data.hourly.cloud_cover)
        else None,
    ),
    OpenMeteoCustomSensorEntityDescription(
        key="wind_gust",
        name="Wind Gust",
        translation_key="wind_gust",
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.KILOMETERS_PER_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data, idx: data.hourly.wind_gusts_10m[idx]
        if data.hourly and data.hourly.wind_gusts_10m and idx < len(data.hourly.wind_gusts_10m)
        else None,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OpenMeteoCustomConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Open-Meteo Custom sensor entities based on a config entry."""
    coordinator = entry.runtime_data
    async_add_entities(
        OpenMeteoCustomSensorEntity(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class OpenMeteoCustomSensorEntity(
    CoordinatorEntity[OpenMeteoCustomDataUpdateCoordinator], SensorEntity
):
    """Representation of an Open-Meteo Custom sensor."""

    entity_description: OpenMeteoCustomSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OpenMeteoCustomDataUpdateCoordinator,
        entry: OpenMeteoCustomConfigEntry,
        description: OpenMeteoCustomSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"

        model = entry.data.get(CONF_MODEL, "best_match")
        model_label = MODELS.get(model, model)

        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry.entry_id)},
            manufacturer="Open-Meteo",
            name=entry.title,
            model=model_label,
        )

    @property
    def native_value(self) -> float | int | None:
        """Return the state of the sensor."""
        idx = self.coordinator.current_hourly_index
        if idx is None or not self.coordinator.data:
            return None
        return self.entity_description.value_fn(self.coordinator.data, idx)
