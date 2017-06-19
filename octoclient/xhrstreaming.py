import json
from threading import Thread

import requests

from octoclient.sockjsclient import SockJSClient


class XHRStreamingEventHandler(SockJSClient):
    """
    Class for SockJS communication with XHRStreaming method

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
    def __init__(self, url,
                 on_open=None, on_close=None, on_message=None, session=None):

        super().__init__(url, on_open, on_close, on_message)

        self.socket = session or requests.Session()

    def run(self):
        """
        Runs thread, which listens on socket.
        Executes given callbacks on events
        """
        self.thread = Thread(target=self._xhr_streaming_run)
        self.thread.daemon = True
        self.thread.start()

    def _xhr_streaming_run(self):
        """
        Function for getting data and executing callbacks
        """
        url = self.url.format(protocol="https" if self.secure else "http",
                              method="xhr_streaming")
        while True:
            try:
                connection = self.socket.post(url, stream=True)
                for line in connection.iter_lines():
                    line = line.decode('utf-8')
                    if line.startswith('o'):
                        self.on_open(self)
                    elif line.startswith('c'):
                        self.on_close(self)
                    elif line.startswith('m'):
                        data = json.loads(line[1:])
                        self.on_message(self, data)
                    elif line.startswith('a'):
                        for msg in json.loads(line[1:]):
                            self.on_message(self, msg)
            finally:
                connection.close()

    def send(self, data):
        """
        Sends data, currently not working properly.
        OctoPrint server returns 404.
        """
        url = self.url.format(protocol="https" if self.secure else "http",
                              method="xhr_send")
        response = self.socket.post(url, data=json.dumps(data))
        return response
