import time
import os
from itertools import chain, combinations

import pytest
from betamax import Betamax
from betamax_serializers import pretty_json

from octoclient import OctoClient


URL = 'http://printer15.local'
APIKEY = 'YouShallNotPass'

with Betamax.configure() as config:
    config.cassette_library_dir = 'tests/fixtures/cassettes'
    record_mode = os.environ.get('RECORD', 'none')
    config.default_cassette_options['record_mode'] = record_mode
    config.match_options = {'uri', 'method', 'body', 'query'}
    Betamax.register_serializer(pretty_json.PrettyJSONSerializer)
    config.default_cassette_options['serialize_with'] = 'prettyjson'


def sleep(seconds):
    '''
    If recording, sleep for a given amount of seconds
    '''
    if 'RECORD' in os.environ:
        time.sleep(seconds)


def subsets(*items):
    '''
    Get all possible subsets of something
    '''
    N = len(items)+1
    return chain(*map(lambda x: combinations(items, x), range(0, N)))


def zero(component):
    '''
    Add a 0 at the end of the component, if it is tool
    '''
    return 'tool0' if component == 'tool' else component


@pytest.mark.usefixtures('betamax_session')
@pytest.fixture
def client(betamax_session):
    return OctoClient(url=URL, apikey=APIKEY, session=betamax_session)


@pytest.fixture
def gcode():
    class GCode:
        def __init__(self, filename):
            self.filename = filename
            self.path = 'tests/fixtures/gcodes/{}'.format(filename)

    return GCode('homex.gcode')


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

    @pytest.mark.parametrize('filename', ('hodorstop.gcode', 'plate2.gcode'))
    def test_info_for_specific_file(self, client, filename):
        f = client.files(filename)
        assert f['name'] == filename

    @pytest.mark.parametrize('filename', ('nietzsche.gcode', 'noexist.gcode'))
    def test_nonexisting_file_raises(self, client, filename):
        with pytest.raises(RuntimeError):
            client.files(filename)

    def test_upload_by_path(self, client, gcode):
        f = client.upload(gcode.path)
        assert f['done']
        assert f['files']['local']['name'] == gcode.filename
        client.delete(gcode.filename)

    def test_upload_file_object(self, client, gcode):
        with open(gcode.path) as fo:
            f = client.upload(('fake.gcode', fo))
        assert f['done']
        assert f['files']['local']['name'] == 'fake.gcode'
        client.delete('fake.gcode')

    def test_upload_and_select(self, client, gcode):
        f = client.upload(gcode.path, select=True)
        assert f['done']
        assert f['files']['local']['name'] == gcode.filename
        selected = client.job_info()['job']['file']['name']
        assert selected == gcode.filename
        client.delete(gcode.filename)

    def test_upload_and_print(self, client, gcode):
        f = client.upload(gcode.path, print=True)
        assert f['done']
        assert f['files']['local']['name'] == gcode.filename
        selected = client.job_info()['job']['file']['name']
        assert selected == gcode.filename
        assert client.state() == 'Printing'
        sleep(5)
        client.delete(gcode.filename)

    def test_upload_and_select_one_by_one(self, client, gcode):
        client.upload(gcode.path)
        client.select(gcode.filename)
        selected = client.job_info()['job']['file']['name']
        assert selected == gcode.filename
        client.delete(gcode.filename)

    def test_upload_and_select_with_print_one_by_one(self, client, gcode):
        client.upload(gcode.path)
        client.select(gcode.filename, print=True)
        selected = client.job_info()['job']['file']['name']
        assert selected == gcode.filename
        assert client.state() == 'Printing'
        sleep(5)
        client.delete(gcode.filename)

    def test_upload_and_select_and_print_one_by_one(self, client, gcode):
        client.upload(gcode.path)
        client.select(gcode.filename)
        selected = client.job_info()['job']['file']['name']
        assert selected == gcode.filename
        client.print()
        assert client.state() == 'Printing'
        sleep(5)
        client.delete(gcode.filename)

    def test_upload_print_pause_cancel(self, client, gcode):
        client.upload(gcode.path)
        client.select(gcode.filename, print=True)
        sleep(1)
        client.pause()
        assert client.state() == 'Paused'
        sleep(1)
        client.cancel()
        sleep(1)
        client.delete(gcode.filename)

    def test_upload_print_pause_restart(self, client, gcode):
        client.upload(gcode.path)
        client.select(gcode.filename, print=True)
        sleep(1)
        client.pause()
        sleep(1)
        client.restart()
        assert client.state() == 'Printing'
        sleep(5)
        client.delete(gcode.filename)

    def test_connection_info(self, client):
        info = client.connection_info()

        assert 'current' in info
        assert 'baudrate' in info['current']
        assert 'port' in info['current']
        assert 'state' in info['current']

        assert 'options' in info
        assert 'baudrates' in info['options']
        assert 'ports' in info['options']

    def test_disconnect(self, client):
        client.disconnect()
        assert client.state() in ['Offline', 'Closed']

    def test_connect(self, client):
        '''
        Since it's hard with betamax fixture to check state() multiple times
        in one test, this test hopes test_disconnect() was called before it.
        It is not possible to run it without it in record mode.
        TODO Fix this
        '''
        client.connect()
        assert client.state() in ['Connecting',
                                  'Operational',
                                  'Opening serial port']

    def test_fake_ack(self, client):
        client.fake_ack()
        # TODO What to check?

    def test_logs(self, client):
        logs = client.logs()
        assert 'files' in logs
        assert 'free' in logs
        assert isinstance(logs['free'], int)

    def test_delete_log(self, client):
        client.delete_log('serial.log')
        logs = client.logs()
        for log in logs['files']:
            assert log['name'] != 'serial.log'

    def test_printer(self, client):
        printer = client.printer()
        assert 'ready' in printer['sd']
        assert printer['state']['flags']['operational']
        assert printer['state']['flags']['ready']
        assert not printer['state']['flags']['error']
        assert not printer['state']['flags']['printing']
        assert 'bed' in printer['temperature']
        assert 'tool0' in printer['temperature']
        assert 'history' not in printer['temperature']

    @pytest.mark.parametrize('exclude', subsets('sd', 'temperature', 'state'))
    def test_printer_with_excluded_stuff(self, client, exclude):
        printer = client.printer(exclude=exclude)
        for key in exclude:
            assert key not in printer
        assert len(printer) == 3 - len(exclude)

    def test_printer_with_history(self, client):
        printer = client.printer(history=True)
        assert isinstance(printer['temperature']['history'], list)

    @pytest.mark.parametrize('limit', range(1, 4))
    def test_printer_with_history_and_limit(self, client, limit):
        printer = client.printer(history=True, limit=limit)
        assert len(printer['temperature']['history']) == limit

    @pytest.mark.parametrize('key', ('actual', 'target', 'offset'))
    @pytest.mark.parametrize('component', ('tool', 'bed'))
    def test_tool_and_bed(self, client, key, component):
        info = getattr(client, component)()  # client.tool() or bed()
        assert 'history' not in info
        assert isinstance(info[zero(component)][key], (float, int))

    @pytest.mark.parametrize('key', ('actual', 'target'))
    @pytest.mark.parametrize('component', ('tool', 'bed'))
    def test_tool_and_bed_with_history(self, client, key, component):
        info = getattr(client, component)(history=True)
        assert 'history' in info
        for h in info['history']:
            assert isinstance(h[zero(component)][key], (float, int))

    @pytest.mark.parametrize('limit', range(1, 4))
    @pytest.mark.parametrize('component', ('tool', 'bed'))
    def test_tool_and_bed_with_history_limit(self, client, limit, component):
        info = getattr(client, component)(history=True, limit=limit)
        assert len(info['history']) == limit

    def test_home_all(self, client):
        # we are only testing if no exception occurred, there's no return
        client.home()

    @pytest.mark.parametrize('axes', (('x',), ('y',), ('z',), ('x', 'y',)))
    def test_home_some(self, client, axes):
        # we are only testing if no exception occurred, there's no return
        client.home(axes)

    @pytest.mark.parametrize('coordinates', ((20, 0, 0), (0, 20, 0)))
    def test_jog(self, client, coordinates):
        # we are only testing if no exception occurred, there's no return
        client.jog(*coordinates)
