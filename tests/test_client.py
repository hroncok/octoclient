import pytest
from betamax import Betamax

from octoclient import OctoClient


URL = 'http://printer15.local'
APIKEY = 'YouShallNotPass'

with Betamax.configure() as config:
    config.cassette_library_dir = 'tests/fixtures/cassettes'


@pytest.mark.usefixtures('betamax_session')
class TestClient:
    def test_init_works_with_good_auth(self, betamax_session):
        # Should not raise anything
        oc = OctoClient(url=URL, apikey=APIKEY, session=betamax_session)

    def test_init_raises_with_bad_auth(self, betamax_session):
        with pytest.raises(RuntimeError):
            oc = OctoClient(url=URL, apikey='nope', session=betamax_session)
