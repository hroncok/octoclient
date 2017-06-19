import json
from threading import Thread

import websocket

from octoclient.sockjsclient import SockJSClient


class WebSocketEventHandler(SockJSClient):
    """
    Class for SockJS WebSocket communication

    params:
    url - url of Printer
    on_open - callback function with 1 argument, api of WebSocketApp
            - executes on creating new connection
    on_close - callback function with 1 argument, api of WebSocketApp
             - executes on connection close
    on_message - callback function with 2 arguments, api of WebSocketApp
                 and message in dict format
               - executes on received message, if array, then it executes
                 for every value of given array
    """
    def __init__(self, url, on_open=None, on_close=None, on_message=None):
        super().__init__(url, on_open, on_close, on_message)

        self.url = self.url.format(protocol="wss" if self.secure else "ws",
                                   method="websocket")

    def run(self):
        """
        Runs thread, which listens on socket.
        Executes given callbacks on events
        """
        def on_message(ws, data):
            if data.startswith('m'):
                self.on_message(ws, json.loads(data[1:]))
            elif data.startswith('a'):
                for msg in json.loads(data[1:]):
                    self.on_message(ws, msg)

        self.socket = websocket.WebSocketApp(self.url,
                                             on_open=self.on_open,
                                             on_close=self.on_close,
                                             on_message=on_message)
        self.thread = Thread(target=self.socket.run_forever)
        self.thread.daemon = True
        self.thread.start()

    def send(self, data):
        """
        Sends data, currently not working properly.
        OctoPrint server is unable to parse.
        """
        self.socket.send(json.dumps(data))
