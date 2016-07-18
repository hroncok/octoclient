from urllib import parse as urlparse

import requests


class OctoClient:
    '''
    Encapsulates communication with one OctoPrint instance
    '''

    def __init__(self, *, url=None, apikey=None, session=None):
        '''
        Initialize the object with URL and API key

        If a session is provided, it will be used (mostly for testing)
        '''
        if not url:
            raise TypeError('Required argument \'url\' not found or emtpy')
        if not apikey:
            raise TypeError('Required argument \'apikey\' not found or emtpy')

        parsed = urlparse.urlparse(url)
        if parsed.scheme not in ['http', 'https']:
            raise TypeError('Provided URL is not HTTP(S)')
        if not parsed.netloc:
            raise TypeError('Provided URL is empty')

        self.url = '{}://{}'.format(parsed.scheme, parsed.netloc)

        self.session = session or requests.Session()
        self.session.headers.update({'X-Api-Key': apikey})

        # Try a simple request to see if the API key works
        # Keep the info, in case we need it later
        self.version = self.version()

    def _get(self, path):
        '''
        Perform HTTP GET on given path with the auth header

        Path shall be the ending part of the URL,
        i.e. it should not be full URL

        Raises a RuntimeError when not 200 OK

        Return JSON decoded data
        '''
        url = urlparse.urljoin(self.url, path)
        response = self.session.get(url)

        if response.status_code != 200:
            error = response.text
            msg = 'Reply for {} was not OK: {} ({})'
            msg = msg.format(url, error, response.status_code)
            raise RuntimeError(msg)

        return response.json()

    def version(self):
        '''
        Retrieve information regarding server and API version
        '''
        return self._get('/api/version')
