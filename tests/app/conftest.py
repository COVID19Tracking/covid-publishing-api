import pytest
from app import create_app, db
from decouple import config

@pytest.fixture
def app():
    env_config = config("ENV", cast=str, default="unittestpostgresql")
    app = create_app(env_config);
    # create the database and load test data
    # once we're ready to start testing with the db, setup the database
    # with an initial schema
#     with app.app_context():
#         init_db()
#         get_db().executescript(_data_sql)

    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
