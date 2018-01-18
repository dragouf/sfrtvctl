import base64
import json
import logging
import socket
import time

from . import exceptions


URL_FORMAT = "ws://{}:{}"

_mappings = [
    ["KEY_POWEROFF",      {"Params":{"Token":"LAN","DeviceSoftVersion":"11.2.2","Action":"ButtonEvent","Press":[303],"DeviceModel":"iPhone"}},         "Power off"],
    ["KEY_UP",            "Up",        "Up"],
    ["KEY_DOWN",          "Down",      "Down"],
    ["KEY_LEFT",          "Left",      "Left"],
]

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

        self._read_response()

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

    def control(self, key):
        """Send a control command."""
        if not self.connection:
            raise exceptions.ConnectionClosed()

        jsonTrame = mapping[0][1]
        payload = json.dumps(jsonTrame)

        logging.info("Sending command")
        self.connection.send(payload)
        time.sleep(self._key_interval)

    _key_interval = 0.5

    def _read_response(self):
        response = self.connection.recv()
        response = json.loads(response)

        logging.debug("Access granted.")

    @staticmethod
    def _serialize_string(string):
        if isinstance(string, str):
            string = str.encode(string)

        return base64.b64encode(string).decode("utf-8")
