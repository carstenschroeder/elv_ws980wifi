import logging

import voluptuous as vol

from . import DOMAIN, CONF_FACTOR

# Import the device class from the component that you want to support
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
    PLATFORM_SCHEMA,
    SensorEntity
)
from homeassistant.const import (
    UnitOfIrradiance,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolumetricFlux,
    PERCENTAGE,
    LIGHT_LUX,
    CONF_NAME,
    CONF_UNIT_OF_MEASUREMENT
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity


_LOGGER = logging.getLogger(__name__)

# SCAN_INTERVAL = timedelta(minutes=1)

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_NAME): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=''): cv.string,
    vol.Optional(CONF_FACTOR): vol.Coerce(float),
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the Keba KeContact platform."""

    # Assign configuration variables. The configuration check takes care they are
    # present. 
    name = config.get(CONF_NAME)
    unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT)
    factor = config.get(CONF_FACTOR)

    for gateway in hass.data[DOMAIN].values():
        # Verify that passed in configuration works
        if gateway.is_valid:
            # Add devices
            add_entities([ELV_ws980wifi_Sensor(name, unit_of_measurement, factor, gateway)], True)
        else:
            _LOGGER.error("No valid data received from weather station")


class ELV_ws980wifi_Sensor(SensorEntity):

    def __init__(self, name, unit_of_measurement, factor, gateway):
        self._fieldname = name
        self._factor = factor
        self._gateway = gateway
        
        self._attr_native_value = None
        self._attr_name = gateway.name + '_' + name
        self._attr_unique_id = gateway.name + '_' + name
        self._attr_native_unit_of_measurement = unit_of_measurement

        if unit_of_measurement == "°C":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        elif unit_of_measurement == "mbar":
            self._attr_device_class = SensorDeviceClass.PRESSURE
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = UnitOfPressure.MBAR
        elif unit_of_measurement == "%":
            self._attr_device_class = SensorDeviceClass.HUMIDITY
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = PERCENTAGE
        elif unit_of_measurement == "lux":
            self._attr_device_class = SensorDeviceClass.ILLUMINANCE
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = LIGHT_LUX
        elif unit_of_measurement == "W/m2":
            self._attr_device_class = SensorDeviceClass.IRRADIANCE
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = UnitOfIrradiance.WATTS_PER_SQUARE_METER
        elif self._fieldname == "rain_rate":
            self._attr_device_class = SensorDeviceClass.PRECIPITATION_INTENSITY 
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_native_unit_of_measurement = UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR
        elif self._fieldname in ("rain_day", "rain_week", "rain_month", "rain_year", "rain_totals"):
            self._attr_device_class = SensorDeviceClass.PRECIPITATION
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING 
            self._attr_native_unit_of_measurement = UnitOfPrecipitationDepth.MILLIMETERS
        elif self._fieldname in ("wind_speed", "gust_speed"):
            self._attr_device_class = SensorDeviceClass.WIND_SPEED 
            self._attr_state_class = SensorStateClass.MEASUREMENT 
            self._attr_native_unit_of_measurement = UnitOfSpeed.KILOMETERS_PER_HOUR 
            self._factor = 3.6

        self.update()

    def update(self):
        """Update value of sensor."""
        try:
            if self._gateway.is_valid:
                self._attr_native_value = self._gateway.getweatherdata(self._fieldname)
                if self._factor is not None:
                    self._attr_native_value = round(self._attr_native_value * self._factor, 2)
            else:
                self._attr_native_value = None
        except Exception as ex:
            _LOGGER.error(ex)
