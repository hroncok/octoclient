import os

import pytest
from betamax import Betamax

from octoclient import OctoClient


URL = 'http://printer15.local'
APIKEY = 'YouShallNotPass'

with Betamax.configure() as config:
    config.cassette_library_dir = 'tests/fixtures/cassettes'
    record_mode = os.environ.get('RECORD', 'none')
    config.default_cassette_options['record_mode'] = record_mode


@pytest.mark.usefixtures('betamax_session')
@pytest.fixture
def client(betamax_session):
    return OctoClient(url=URL, apikey=APIKEY, session=betamax_session)


def gcode(filename):
    return 'tests/fixtures/gcodes/{}'.format(filename)


class TestClient:
    @pytest.mark.usefixtures('betamax_session')
    def test_init_works_with_good_auth(self, betamax_session):
        # Should not raise anything
        OctoClient(url=URL, apikey=APIKEY, session=betamax_session)

    @pytest.mark.usefixtures('betamax_session')
    def test_init_raises_with_bad_auth(self, betamax_session):
        with pytest.raises(RuntimeError):
            OctoClient(url=URL, apikey='nope', session=betamax_session)

    def test_files_contains_files_and_free_space_info(self, client):
        files = client.files()
        assert 'hodorstop.gcode' in [f['name'] for f in files['files']]
        assert isinstance(files['free'], int)

    def test_files_local_works(self, client):
        files = client.files('local')
        assert 'hodorstop.gcode' in [f['name'] for f in files['files']]
        assert isinstance(files['free'], int)

    def test_files_sdcard_works(self, client):
        files = client.files('sdcard')
        assert files['files'] == []  # no files on sdcard
        assert 'free' not in files  # API doesn't report that back

    def test_files_bogus_location_raises(self, client):
        with pytest.raises(RuntimeError):
            client.files('fantomas')

    @pytest.mark.parametrize('filename', ('hodorstop.gcode', 'plate2.gcode'))
    def test_info_for_specific_file(self, client, filename):
        f = client.files('local/{}'.format(filename))
        assert f['name'] == filename

    @pytest.mark.parametrize('filename', ('nietzsche.gcode', 'noexist.gcode'))
    def test_nonexisting_file_raises(self, client, filename):
        with pytest.raises(RuntimeError):
            client.files('local/{}'.format(filename))

    @pytest.mark.parametrize('filename', ('homex.gcode',))
    def test_upload_by_path(self, client, filename):
        f = client.upload(gcode(filename))
        assert f['done']
        assert f['files']['local']['name'] == filename
