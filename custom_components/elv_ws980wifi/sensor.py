import logging

import voluptuous as vol

from . import DOMAIN, CONF_FACTOR

# Import the device class from the component that you want to support
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import CONF_NAME, CONF_UNIT_OF_MEASUREMENT
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


class ELV_ws980wifi_Sensor(Entity):

    def __init__(self, name, unit_of_measurement, factor, gateway):
        self._fieldname = name
        self._name = gateway.name + '_' + name
        self._unique_id = gateway.name + '_' + name
        self._unit_of_measurement = unit_of_measurement
        self._factor = factor
        self._gateway = gateway
        self._state = None

        self.update()

    @property
    def name(self):
        """Return the display name of this sensor."""
        return self._name

    @property
    def unique_id(self):
        """Return an unique identifier for this entity."""
        return self._unique_id

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement


    def update(self):
        """Update state of sensor."""
        try:
            if self._gateway.is_valid:
                self._state = self._gateway.getweatherdata(self._fieldname)
                if self._factor is not None:
                    self._state = round(self._state * self._factor, 2)
            else:
                self._state = None
        except Exception as ex:
            _LOGGER.error(ex)
