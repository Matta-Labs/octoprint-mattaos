import json
import logging
import websocket

_logger = logging.getLogger("octoprint.plugins.mattaconnect")


class Socket:
    def __init__(self, on_message, url, token):
        self.connect(on_message, url, token)

    def run(self):
        try:
            self.socket.run_forever()
        except Exception as e:
            _logger.info("ERROR Socket run: %s", e)
            self.disconnect()

    def send_msg(self, msg):
        try:
            if isinstance(msg, dict):
                msg = json.dumps(msg)
            if self.connected() and self.socket is not None:
                self.socket.send(msg)
        except Exception as e:
            _logger.info("ERROR Socket send_msg: %s", e)
            self.disconnect()

    def connected(self):
        return self.socket and self.socket.sock and self.socket.sock.connected

    def connect(self, on_message, url, token):
        url = url + "?token=" + token
        self.socket = websocket.WebSocketApp(
            url,
            on_message=on_message,
        )

    def disconnect(self):
        try:
            self.socket.keep_running = False
            self.socket.close()
            self.socket = None
        except Exception as e:
            _logger.info("ERROR Socket disconnect: %s", e)
