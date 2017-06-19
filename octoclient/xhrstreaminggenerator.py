import json
import random
import string
from urllib import parse as urlparse

import requests


class XHRStreamingGenerator:
    """
    Class that can communicate to SockJS server with XHR streaming
    """

    @classmethod
    def random_str(cls, length):
        letters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(letters) for c in range(length))

    def __init__(self, url, session=None):
        """
        Initialize the connection
        The url shall include the protocol and port (if necessary)
        """
        self.session = session or requests.Session()
        r1 = str(random.randint(0, 1000))
        conn_id = self.random_str(8)
        self.base_url = url
        self.url = '/'.join((urlparse.urljoin(url, 'sockjs'), r1, conn_id))

    def info(self):
        url = urlparse.urljoin(self.base_url, 'sockjs/info')
        response = self.session.get(url)
        return response.json()

    def read_loop(self):
        """
        Creates generator object
        """
        url = '/'.join((self.url, 'xhr_streaming'))
        while True:
            try:
                connection = self.session.post(url, stream=True)
                for line in connection.iter_lines():
                    line = line.decode('utf-8')
                    if line.startswith('o'):
                        continue  # open connection
                    if line.startswith('c'):
                        continue  # close connection
                    if line.startswith('h'):
                        continue  # heartbeat
                    if line.startswith('m'):
                        yield json.loads(line[1:])
                        continue  # message
                    if line.startswith('a'):
                        for msg in json.loads(line[1:]):
                            yield msg
                        continue  # array
            finally:
                connection.close()

    def send(self, data):
        """
        Sends data, currently not working properly.
        OctoPrint server returns 404
        """
        url = '/'.join((self.url, 'xhr_send'))
        response = self.session.post(url, data=json.dumps(data))
        return response
