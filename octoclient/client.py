from contextlib import contextmanager
import os
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

        Raises a RuntimeError when not 20x OK-ish

        Returns JSON decoded data
        '''
        url = urlparse.urljoin(self.url, path)
        response = self.session.get(url)
        self._check_response(response)

        return response.json()

    def _post(self, path, data=None, files=None):
        '''
        Perform HTTP POST on given path with the auth header

        Path shall be the ending part of the URL,
        i.e. it should not be full URL

        Raises a RuntimeError when not 20x OK-ish

        Returns JSON decoded data
        '''
        url = urlparse.urljoin(self.url, path)
        response = self.session.post(url, data=data, files=files)
        self._check_response(response)

        return response.json()

    def _check_response(self, response):
        '''
        Make sure the response status code was 20x, raise otherwise
        '''
        if not (200 <= response.status_code < 210):
            error = response.text
            msg = 'Reply for {} was not OK: {} ({})'
            msg = msg.format(response.url, error, response.status_code)
            raise RuntimeError(msg)
        return response

    def version(self):
        '''
        Retrieve information regarding server and API version
        '''
        return self._get('/api/version')

    def files(self, location=None):
        '''
        Retrieve information regarding all files currently available and
        regarding the disk space still available locally in the system

        If location is used, retrieve information regarding the files currently
        available on the selected location and - if targeting the local
        location - regarding the disk space still available locally in the
        system

        If location is a file, retrieves the selected file''s information
        '''
        if location:
            return self._get('/api/files/{}'.format(location))
        return self._get('/api/files')

    @contextmanager
    def _file_tuple(self, file):
        '''
        Yields a tuple with filename and file object

        Expects the same thing or a path as input
        '''
        mime = 'application/octet-stream'

        try:
            exists = os.path.exists(file)
        except:
            exists = False

        if exists:
            filename = os.path.basename(file)
            with open(file, 'rb') as f:
                yield (filename, f, mime)
        else:
            yield file + (mime,)

    def upload(self, file, *, location='local',
               select=False, print=False, userdata=None):
        '''
        Upload a given file
        It can be a path or a tuple with a filename and a file-like object
        '''
        with self._file_tuple(file) as file_tuple:
            files = {'file': file_tuple}
            data = {'select': str(select).lower(), 'print': str(print).lower()}
            if userdata:
                data['userdata'] = userdata

            return self._post('/api/files/{}'.format(location),
                              files=files, data=data)
