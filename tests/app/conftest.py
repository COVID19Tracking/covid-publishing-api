import pytest
from app import create_app, db

import testing.postgresql

class TestingPostgresqlConfig:
    def __init__(self):
        # TODO(asilverstein): Clean up after ourself
        self.test_db = testing.postgresql.Postgresql()

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return self.test_db.url()

    SQLALCHEMY_TRACK_MODIFICATIONS = False

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
def client(app):
    """A test client for the app."""
    return app.test_client()
