import pytest
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