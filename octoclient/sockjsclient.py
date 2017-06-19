import random
import string

from urllib import parse as urlparse


class SockJSClient:
    """
    Abstract class for SockJS client event handlers
    """
    @classmethod
    def random_str(cls, length):
        """
        Produces random string of given length
        It is used for session ID
        unique for every session of SockJS connection
        """
        letters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(letters) for c in range(length))

    def __init__(self, url, on_open=None, on_close=None, on_message=None):
        self.on_open = on_open if callable(on_open) else lambda x: None
        self.on_close = on_close if callable(on_close) else lambda x: None
        self.on_message = \
            on_message if callable(on_message) else lambda x, y: None

        self.thread = None
        self.socket = None

        parsed_url = urlparse.urlparse(url)
        self.base_url = parsed_url.netloc
        self.secure = True if parsed_url.scheme in ["wss", "https"] else False

        server_id = str(random.randint(0, 1000))
        session_id = self.random_str(8)
        self.url = "{protocol}://" + \
                   "/".join((self.base_url, "sockjs", server_id, session_id)) \
                   + "/{method}"

    def wait(self):
        self.thread.join()

    def run(self):
        """Initializes and starts thread and socket communication"""
        raise NotImplementedError("Should have implemented this")

    def send(self, data):
        """Send data across socket communication"""
        raise NotImplementedError("Should have implemented this")
