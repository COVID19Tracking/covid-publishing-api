import pytest
from unittest import mock
from unittest.mock import MagicMock
from app import create_app, db
from app.auth.auth_cli import getToken

import testing.postgresql

class TestingPostgresqlConfig:
    def __init__(self):
        # TODO(asilverstein): Clean up after ourself
        self.test_db = testing.postgresql.Postgresql()

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return self.test_db.url()

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SECRET_KEY = '12345'

    API_WEBHOOK_URL = None

    # the actual Slack SDK is mocked out below, so these don't matter as long as they exist
    SLACK_API_TOKEN = 'dummy_token'
    SLACK_CHANNEL = 'some_channel'

    @staticmethod
    def init_app(app):
        pass


@pytest.fixture
def app():
    conf = TestingPostgresqlConfig()
    app = create_app(conf);
    with app.app_context():
       # Let SQLAlchemy do its thing and initialize the database
       db.create_all()

    yield app

@pytest.fixture
def headers(app):
    with app.app_context():
        auth_token = getToken('testing')
        
    headers = {
        'Authorization': 'Bearer {}'.format(auth_token)
    }
    
    yield headers

# autouse=True ensures that Slack is mocked out in the entire test suite and not actually called
@pytest.fixture(autouse=True)
def slack_mock():
    client_mock = MagicMock()
    with mock.patch('app.utils.slacknotifier.WebClient', return_value=client_mock) as _fixture:
        yield client_mock
