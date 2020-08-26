"""Support for ELV WS980Wifi weather station"""
import logging

from datetime import timedelta

import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.const import CONF_DEVICES, CONF_NAME, CONF_HOST, CONF_PORT
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.event import track_time_interval

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)

CONF_FACTOR = "factor"

DOMAIN = 'elv_ws980wifi'

# Validation of the user's configuration
DEVICE_CONFIG = vol.Schema({
    vol.Optional(CONF_NAME, default='elv_ws980wifi'): cv.string,
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_PORT): cv.port,
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_DEVICES): vol.All(cv.ensure_list, [DEVICE_CONFIG]),
    })
}, extra=vol.ALLOW_EXTRA)

ITEM_INTEMP = 0x01  # C
ITEM_OUTTEMP = 0x02  # C
ITEM_DEWPOINT = 0x03  # C
ITEM_WINDCHILL = 0x04  # C
ITEM_HEATINDEX = 0x05  # C
ITEM_INHUMI = 0x06  # %
ITEM_OUTHUMI = 0x07  # %
ITEM_ABSBARO = 0x08  # mbar
ITEM_RELBARO = 0x09  # mbar
ITEM_WINDDIRECTION = 0x0a  # degree
ITEM_WINDSPEED = 0x0b  # m/s
ITEM_GUSTSPEED = 0x0c  # m/s
ITEM_RAINEVENT = 0x0d  # mm
ITEM_RAINRATE = 0x0e  # mm/h
ITEM_RAINHOUR = 0x0f  # mm
ITEM_RAINDAY = 0x10  # mm
ITEM_RAINWEEK = 0x11  # mm
ITEM_RAINMONTH = 0x12  # mm
ITEM_RAINYEAR = 0x13  # mm
ITEM_RAINTOTALS = 0x14  # mm
ITEM_LIGHT = 0x15  # lux
ITEM_UV = 0x16  # uW/m^2
ITEM_UVI = 0x17  # 0-15 index


# this map associates the item identifier with [label, num_bytes, function]
# required for decoding weather data from raw bytes.
ITEM_MAPPING = {
    ITEM_INTEMP: ['in_temp', 2, lambda x: x / 10.0],
    ITEM_OUTTEMP: ['out_temp', 2, lambda x: x / 10.0],
    ITEM_DEWPOINT: ['dewpoint', 2, lambda x: x / 10.0],
    ITEM_WINDCHILL: ['windchill', 2, lambda x: x / 10.0],
    ITEM_HEATINDEX: ['heatindex', 2, lambda x: x / 10.0],
    ITEM_INHUMI: ['in_humidity', 1, lambda x: x],
    ITEM_OUTHUMI: ['out_humidity', 1, lambda x: x],
    ITEM_ABSBARO: ['abs_baro', 2, lambda x: x / 10.0],
    ITEM_RELBARO: ['rel_baro', 2, lambda x: x / 10.0],
    ITEM_WINDDIRECTION: ['wind_dir', 2, lambda x: x],
    ITEM_WINDSPEED: ['wind_speed', 2, lambda x: x / 10.0],
    ITEM_GUSTSPEED: ['gust_speed', 2, lambda x: x / 10.0],
    ITEM_RAINEVENT: ['rain_event', 4, lambda x: x / 10.0],
    ITEM_RAINRATE: ['rain_rate', 4, lambda x: x / 10.0],
    ITEM_RAINHOUR: ['rain_hour', 4, lambda x: x / 10.0],
    ITEM_RAINDAY: ['rain_day', 4, lambda x: x / 10.0],
    ITEM_RAINWEEK: ['rain_week', 4, lambda x: x / 10.0],
    ITEM_RAINMONTH: ['rain_month', 4, lambda x: x / 10.0],
    ITEM_RAINYEAR: ['rain_year', 4, lambda x: x / 10.0],
    ITEM_RAINTOTALS: ['rain_totals', 4, lambda x: x / 10.0],
    ITEM_LIGHT: ['light', 4, lambda x: x / 10.0],
    ITEM_UV: ['uv', 2, lambda x: x],
    ITEM_UVI: ['uvi', 1, lambda x: x],
}


def setup(hass, config):
    """Set up the ELV WS980wifi  integration."""

    hass.data.setdefault(DOMAIN, {})

    for device_config in config[DOMAIN][CONF_DEVICES]:
        name = device_config.get(CONF_NAME)
        host = device_config.get(CONF_HOST)
        port = device_config.get(CONF_PORT)

        try:
            gateway = ELV_ws980wifi_Gateway(host, port, name)
            hass.data[DOMAIN][name] = gateway
        except Exception as ex:
            _LOGGER.error(ex)

    def refresh(event_time):
        """Refresh"""
        _LOGGER.debug("Updating...")
        try:
            for gateway in hass.data[DOMAIN].values():
                gateway.update()
        except Exception as ex:
            _LOGGER.error(ex)

    track_time_interval(hass, refresh, SCAN_INTERVAL)

    return True


def _calc_checksum(index1, index2, b):
    s = 0
    for i in range(index1, index2):
        s += b[i]
    return s % 256


def _fmt(buf):
    if buf:
        return "%s (len=%s)" % (' '.join(["%02x" % x for x in buf]), len(buf))
    return ''


def _decode_bytes(buf, idx, nbytes, func):
    # if all bytes are 0xff, the value is not valid...
    for j in range(nbytes):
        if buf[idx + j] != 0xff:
            break
    else:
        return None
    # ...otherwise, calculate a value from the bytes, MSB first
    x = 0
    for j in range(nbytes):
        x += buf[idx + j] << ((nbytes - j - 1) * 8)
    return func(x)


def decode_weather_data(raw):
    # decode a sequence of bytes into current weather data.  the sequence
    # can be variable length.  an identifier byte is followed by one to
    # four data bytes.  identifier bytes have a value of ITEM_* bitwise
    # or with date and/or time if there is an associated time.
    #
    # so we simply walk the array, decoding as we go.  put the result into
    # a dictionary that contains a dictionary for each observation.
    #
    # if there is a failure, log it and bail out.
    data = dict()
    i = 0
    while i < len(raw):
        item = raw[i]
        i += 1

        label = None
        obs = dict()
        mapping = ITEM_MAPPING.get(item)
        if mapping:
            if i + mapping[1] - 1 >= len(raw):
                _LOGGER.error("not enough bytes for %s: idx=%s nbytes=%s bytes=%s" % (mapping[0], i, mapping[1], raw))
                return None
            # bytes are decoded MSB first, then function is applied
            label = mapping[0]
            obs['value'] = _decode_bytes(raw, i, mapping[1], mapping[2])
            i += mapping[1]
        else:
            _LOGGER.error("no mapping for item id 0x%02x at index %s of %s" % (item, i - 1, _fmt(raw)))
            return None


        # workaround firmware bug for invalid light value
        if (item == ITEM_LIGHT and
                obs['value'] == 0xffffff / 10.0):
            obs['value'] = None

        _LOGGER.debug("%s: %s (0x%02x)" % (label, obs, item))
        data[label] = obs
    return data


class ELV_ws980wifi_Gateway():

    def __init__(self, host, port, name):

        self._name = name
        self._host = host
        self._port = port
        self._server_address = (self._host, self._port)
        self._is_valid = None
        self._weather_data = {}

        self.update()

    @property
    def is_valid(self):
        return self._is_valid

    @property
    def host(self):
        return self._host

    @property
    def name(self):
        return self._name

    def update(self):
        import time
        import socket

        message_get_actuals = b'\xFF\xFF\x0B\x00\x06\x04\x04\x19'

        _LOGGER.debug('sending {!r}'.format(_fmt(message_get_actuals)))

        try:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._sock.settimeout(5)
        except Exception as ex:
            _LOGGER.error(ex)
            raise Exception('Socket error')

        try:
            self._sock.connect(self._server_address)
        except Exception as ex:
            _LOGGER.error(ex)
            data = None
            self._is_valid = False
            self._weather_data = None
            raise Exception('Connection error')
        
        try:
            self._sock.send(message_get_actuals)
            time.sleep(0.1)
            _LOGGER.debug('receiving...')
            data = self._sock.recv(1024)
            _LOGGER.debug('received {!r}'.format(_fmt(data)))
            _LOGGER.debug('checksum {!r}'.format("0x%0.2X" % _calc_checksum(5, 80, data)))
            _LOGGER.debug('checksum {!r}'.format("0x%0.2X" % _calc_checksum(2, 81, data)))
        except Exception as ex:
            _LOGGER.error(ex)
            data = None
            self._is_valid = False
            self._weather_data = None
            raise Exception('Network error')
        finally:
            self._sock.close()

        if _calc_checksum(5, 80, data) != data[80] or _calc_checksum(2, 81, data) != data[81]:
            _LOGGER.error("Checksum mismatch")
            raise Exception('Checksum error')

        self._weather_data = decode_weather_data(data[6:80])

        _LOGGER.debug('weather data {!r}'.format(self._weather_data))

        self._is_valid = self._weather_data is not None

    def getweatherdata(self, name):
        try:
            return self._weather_data[name]['value']
        except KeyError:
            return None
