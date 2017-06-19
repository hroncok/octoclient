import pytest

from octoclient import XHRStreamingEventHandler

from _common import URL


def on_message(api, message):
    api.message = message
    raise RuntimeError


@pytest.mark.usefixtures('betamax_recorder')
@pytest.fixture
def client(betamax_recorder):
    betamax_recorder.current_cassette.match_options.remove('uri')
    session = betamax_recorder.session
    return XHRStreamingEventHandler(url=URL,
                                    session=session,
                                    on_message=on_message)


class TestXHRStreamingGenerator:
    @pytest.mark.usefixtures('betamax_session')
    def test_init_works(self, betamax_session):
        XHRStreamingEventHandler(url=URL, session=betamax_session)

    @pytest.mark.xfail(reason="OctoPrints tornado server returns 404")
    def test_send(self, client):
        r = client.send({"throttle": 10})
        assert r.status_code in [200, 204]

    def test_run(self, client):
        client.run()
        assert client.thread.is_alive()
        client.wait()
        assert client.message.get("connected", None)
