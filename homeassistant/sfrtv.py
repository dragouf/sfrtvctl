"""
Support for interface with a SFR TV (STB7).

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/media_player.sfrtv/
"""
import logging
import socket
from datetime import timedelta

import voluptuous as vol

from homeassistant.components.media_player import (
    SUPPORT_NEXT_TRACK, SUPPORT_PAUSE, SUPPORT_PREVIOUS_TRACK,
    SUPPORT_TURN_OFF, SUPPORT_VOLUME_MUTE, SUPPORT_VOLUME_STEP,
    SUPPORT_VOLUME_SET, SUPPORT_STOP, SUPPORT_SEEK,
    MEDIA_TYPE_VIDEO, MEDIA_TYPE_CHANNEL, SUPPORT_SELECT_SOURCE,
    SUPPORT_PLAY, MediaPlayerDevice, PLATFORM_SCHEMA, SUPPORT_TURN_ON)
from homeassistant.const import (
    CONF_HOST, CONF_NAME, STATE_OFF, STATE_ON, STATE_UNKNOWN, CONF_PORT)
import homeassistant.helpers.config_validation as cv
from homeassistant.util import dt as dt_util

REQUIREMENTS = ['sfrtvctl==0.1.0', 'websocket-client==0.46.0']

_LOGGER = logging.getLogger(__name__)

CONF_TIMEOUT = 'timeout'

DEFAULT_NAME = 'SFR TV Remote'
DEFAULT_PORT = 7682
DEFAULT_TIMEOUT = 5

KNOWN_DEVICES_KEY = 'STB7_known_devices'

SUPPORT_SFRTV = SUPPORT_PAUSE | SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | \
               SUPPORT_PREVIOUS_TRACK | SUPPORT_NEXT_TRACK | SUPPORT_SEEK | \
               SUPPORT_STOP | \
               SUPPORT_PLAY | SUPPORT_VOLUME_STEP

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
    vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
})


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """Set up the SFR TV platform."""
    known_devices = hass.data.get(KNOWN_DEVICES_KEY)
    if known_devices is None:
        known_devices = set()
        hass.data[KNOWN_DEVICES_KEY] = known_devices

    # Is this a manual configuration?
    if config.get(CONF_HOST) is not None:
        host = config.get(CONF_HOST)
        port = config.get(CONF_PORT)
        name = config.get(CONF_NAME)
        timeout = config.get(CONF_TIMEOUT)
    elif discovery_info is not None:
        tv_name = discovery_info.get('name')
        model = discovery_info.get('model_name')
        host = discovery_info.get('host')
        name = "{} ({})".format(tv_name, model)
        port = DEFAULT_PORT
        timeout = DEFAULT_TIMEOUT
    else:
        _LOGGER.warning("Cannot determine device")
        return

    # Only add a device once, so discovered devices do not override manual
    # config.
    ip_addr = socket.gethostbyname(host)
    if ip_addr not in known_devices:
        known_devices.add(ip_addr)
        add_devices([SfrTVDevice(host, port, name, timeout)])
        _LOGGER.info("SFR TV (STB7) %s:%d added as '%s'", host, port, name)
    else:
        _LOGGER.info("Ignoring duplicate SFR TV %s:%d", host, port)


class SfrTVDevice(MediaPlayerDevice):
    """Representation of a SFR TV."""

    def __init__(self, host, port, name, timeout):
        """Initialize the SFR device."""
        from sfrtvctl import exceptions
        from sfrtvctl import Remote

        # Save a reference to the imported classes
        self._exceptions_class = exceptions
        self._remote_class = Remote
        self._name = name
        self._current_source = None
        # Assume that the TV is not muted
        self._muted = False
        # Assume that the TV is in Play mode
        self._playing = True
        self._state = STATE_UNKNOWN
        self._remote = None
        # Mark the end of a shutdown command (need to wait 15 seconds before
        # sending the next command to avoid turning the TV back ON).
        self._end_of_power_off = None
        # Generate a configuration for the SFR library
        self._config = {
            'name': 'HomeAssistant',
            'description': name,
            'id': 'ha.component.sfrtv',
            'port': port,
            'host': host,
            'timeout': timeout,
        }

    def update(self):
        """Retrieve the latest data."""
        # Send an empty key to see if we are still connected
        self.send_key('KEY')

    def get_remote(self):
        """Create or return a remote control instance."""
        if self._remote is None:
            # We need to create a new instance to reconnect.
            self._remote = self._remote_class(self._config)

        return self._remote

    def send_key(self, key, keyArg1, keyArg2):
        """Send a key to the tv and handles exceptions."""
        if self._power_off_in_progress() \
                and not (key == 'POWER'):
            _LOGGER.info("TV is powering off, not sending command: %s", key)
            return
        try:
            self.get_remote().control(key, keyArg1, keyArg2)
            self._state = STATE_ON
        except (self._exceptions_class.UnhandledResponse,
                self._exceptions_class.AccessDenied, BrokenPipeError):
            # We got a response so it's on.
            # BrokenPipe can occur when the commands is sent to fast
            self._state = STATE_ON
            self._remote = None
            return
        except (self._exceptions_class.ConnectionClosed, OSError):
            self._state = STATE_OFF
            self._remote = None
        if self._power_off_in_progress():
            self._state = STATE_OFF

    def _power_off_in_progress(self):
        return self._end_of_power_off is not None and \
               self._end_of_power_off > dt_util.utcnow()

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def supported_features(self):
        """Flag media player features that are supported."""
        return SUPPORT_SFRTV

    def turn_off(self):
        """Turn off media player."""
        self._end_of_power_off = dt_util.utcnow() + timedelta(seconds=15)
        self.send_key('BUTTONEVENT', 'POWER', '')

        # Force closing of remote session to provide instant UI feedback
        try:
            self.get_remote().close()
        except OSError:
            _LOGGER.debug("Could not establish connection.")

    def volume_up(self):
        """Volume up the media player."""
        self.send_key('BUTTONEVENT', 'VUP')

    def volume_down(self):
        """Volume down media player."""
        self.send_key('BUTTONEVENT', 'VDOWN')

    def set_volume_level(self, volume):
        """Set volume level, range 0..1."""
        tv_volume = volume * 100
        self.send_key('SETVOLUME', tv_volume)

    def mute_volume(self, mute):
        """Send mute command."""
        self.send_key('BUTTONEVENT', 'MUTE')

    def media_play_pause(self):
        """Simulate play pause media player."""
        if self._playing:
            self.media_pause()
        else:
            self.media_play()

    def media_play(self):
        """Send play command."""
        self._playing = True
        self.send_key('BUTTONEVENT', 'PLAYPAUSE')

    def media_pause(self):
        """Send media pause command to media player."""
        self._playing = False
        self.send_key('BUTTONEVENT', 'PLAYPAUSE')

    def media_next_track(self):
        """Send next track command."""
        self.send_key('BUTTONEVENT', 'FORWARD')

    def media_previous_track(self):
        """Send the previous track command."""
        self.send_key('BUTTONEVENT', 'REWIND')

    def turn_on(self):
        """Turn the media player on."""
        self.send_key('BUTTONEVENT', 'POWER', '')

    def select_source(self, source):
        """Select input source."""
        self._current_source = source
        self.send_key('ZAP', source)
