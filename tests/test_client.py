import pytest
from betamax import Betamax
from requests import Session

from octoclient import OctoClient


SESSION = Session()
URL = 'http://printer15.local'
APIKEY = 'YouShallNotPass'

with Betamax.configure() as config:
    config.cassette_library_dir = 'tests/fixtures/cassettes'


class TestClient:
    def test_init_works_with_good_auth(self):
        with Betamax(SESSION).use_cassette('init_works_with_good_auth'):
            # Should not raise anything
            oc = OctoClient(url=URL, apikey=APIKEY, session=SESSION)

    def test_init_raises_with_bad_auth(self):
        with Betamax(SESSION).use_cassette('init_raises_with_bad_auth'):
            with pytest.raises(RuntimeError):
                oc = OctoClient(url=URL, apikey='nope', session=SESSION)
