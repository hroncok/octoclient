import os

from betamax import Betamax
from betamax_serializers import pretty_json


URL = 'http://printer15.local'
APIKEY = 'YouShallNotPass'


with Betamax.configure() as config:
    config.cassette_library_dir = 'tests/fixtures/cassettes'
    record_mode = os.environ.get('RECORD', 'none')
    config.default_cassette_options['record_mode'] = record_mode
    config.default_cassette_options['match_requests_on'] = {
        'uri',
        'method',
    }
    Betamax.register_serializer(pretty_json.PrettyJSONSerializer)
    config.default_cassette_options['serialize_with'] = 'prettyjson'
