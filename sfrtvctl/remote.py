import base64
import json
import logging
import socket
import time

from . import exceptions


URL_FORMAT = "ws://{}:{}"

DEVICE_MODEL = "iphone"

_buttonEventmappings = {
    "VUP": 308,
    "VDOWN": 307,
    "RIGHT": 222,
    "LEFT": 293,
    "UP": 297,
    "DOWN": 294,
    "PUP": 290,
    "PDOWN": 291,
    "INFO": 301,
    "RETURN": 27,
    "OK": 13,
    "NUMBER": "THIRDARGUMENT_UTF8DECIMALCODE",
    "PLAYPAUSE": 306,
    "FORWARD": 305,
    "REWIND": 304,
    "MUTE": 302,
    "POWER": 303
}

_appKeymappings = {
    "MOSAIC": "Mosaic",
    "TVGUIDE": "Epg",
    "VOD": "Vod",
    "REPLAY": "Replay",
    "RECORDING": "Pvr",
    "MEDIACENTER": "MediaCenter",
    "SETTINGS": "Settings",
}

_keyboardEventmappings = {
    "SEARCH": 32,
    "VALUE": "THIRDARGUMENT_UTF8DECIMALCODE",
}

_mappings = {
    # use _buttonEventmappings for the value. In case of NUMBER get a third argument as a value
    "BUTTONEVENT": {"Params":{"Token":"LAN","DeviceSoftVersion":"11.2.2","Action":"ButtonEvent","Press":[0],"DeviceModel":"iPhone"}},
    # no conversion for the value, just a digit
    "ZAP": {"Params":{"Token":"LAN","DeviceSoftVersion":"11.2.2","Params":["0","zapdigit"],"Action":"CustomEvent","DeviceModel":"iPhone","Event":"GotoLive"}},
    # use _appKeymappings for the value
    "APP": {"Params":{"Token":"LAN","DeviceSoftVersion":"11.2.2","Action":"GotoApp","AppName":"","DeviceModel":"iPhone","DeviceId":"375CC21F-2E8D-4C31-B728-7790E6D24BD0"}},
    # use number between 1 and 100
    "SETVOLUME": {"Params":{"Token":"LAN","DeviceSoftVersion":"11.2.2","IsMute":False,"Action":"SetVolume","DeviceModel":"iPhone","Level":"12"}},
    # keyboard mode (for example when in search input). Use special key search else use third argument value converted to utf8 decimal code
    "KEYBOARD": {"Params":{"Token":"LAN","DeviceSoftVersion":"11.2.2","Action":"KeyboardEvent","Press":[32],"DeviceModel":"iPhone"}},
    # special packet to ask for STB7 device current state information
    "GETINFO": {"Params":{"Token":"LAN","DeviceSoftVersion":"11.2.2","Action":"GetSessionsStatus","DeviceModel":"iPhone","DeviceId":"375CC21F-2E8D-4C31-B728-7790E6D24BD0"}},
    "GETVERSION": {"Params":{"Token":"LAN","DeviceSoftVersion":"11.2.2","Action":"GetVersions","DeviceModel":"iPhone","DeviceId":"375CC21F-2E8D-4C31-B728-7790E6D24BD0"}}
}

class Remote():
    """Object for remote control connection."""

    def __init__(self, config):
        import websocket

        if not config["port"]:
            config["port"] = 7682

        if config["timeout"] == 0:
            config["timeout"] = None

        url = URL_FORMAT.format(config["host"], config["port"])
        logging.debug("connecting to: %s", url)
        self.connection = websocket.create_connection(url, config["timeout"], subprotocols=["lws-bidirectional-protocol"])

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        """Close the connection."""
        if self.connection:
            self.connection.close()
            self.connection = None
            logging.debug("Connection closed.")

    def control(self, key, keyArg1, keyArg2):
        """Send a control command."""
        if not self.connection:
            raise exceptions.ConnectionClosed()

        if key == "BUTTONEVENT":
            # need a second argument which should be from _buttonEventmappings dic
            if keyArg1 in _buttonEventmappings:
                if keyArg1 != "NUMBER":
                    _mappings[key]["Params"]["Press"][0] = _buttonEventmappings[keyArg1]
                else:
                    _mappings[key]["Params"]["Press"][0] = ord(keyArg2)
            else:
                logging.warn("BUTTONEVENT argument was missing")
        elif key == "ZAP" and keyArg1.isdigit():
            _mappings[key]["Params"]["Params"][0] = int(keyArg1)
        elif key == "APP" and keyArg1 in _appKeymappings:
            _mappings[key]["Params"]["AppName"] = _appKeymappings[keyArg1]
        elif key == "SETVOLUME" and keyArg1.isdigit():
            _mappings[key]["Params"]["Level"] = int(keyArg1)
        elif key == "KEYBOARD" and keyArg1 in _keyboardEventmappings:
            if keyArg1 == "SEARCH":
                _mappings[key]["Params"]["Press"][0] = _keyboardEventmappings[keyArg1]
            else:
                # the utf8 decimal value of the key
                _mappings[key]["Params"]["Press"][0] = ord(keyArg2)

        jsonTrame = _mappings[key]

        payload = json.dumps(jsonTrame)

        logging.info("Sending command: %s", jsonTrame)
        self.connection.send(payload)
        time.sleep(self._key_interval)

    _key_interval = 0.5

    def _read_response(self):
        response = self.connection.recv()
        response = json.loads(response)

        logging.debug("reponse: %s", response)

    @staticmethod
    def _serialize_string(string):
        if isinstance(string, str):
            string = str.encode(string)

        return base64.b64encode(string).decode("utf-8")
