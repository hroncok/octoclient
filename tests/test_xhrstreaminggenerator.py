import pytest

from octoclient import XHRStreamingGenerator

from _common import URL


@pytest.mark.usefixtures('betamax_recorder')
@pytest.fixture
def client(betamax_recorder):
    betamax_recorder.current_cassette.match_options.remove('uri')
    session = betamax_recorder.session
    return XHRStreamingGenerator(url=URL, session=session)


class TestXHRStreamingGenerator:
    @pytest.mark.usefixtures('betamax_session')
    def test_init_works(self, betamax_session):
        XHRStreamingGenerator(url=URL, session=betamax_session)

    def test_info(self, client):
        response = client.info()
        assert response.get("websocket", None) is not None

    @pytest.mark.xfail(reason="OctoPrints tornado server returns 404")
    def test_send(self, client):
        r = client.send({"throttle": 10})
        assert r.status_code in [200, 204]

    def test_readloop(self, client):
        generator = client.read_loop()
        assert next(generator).get("connected", None)
