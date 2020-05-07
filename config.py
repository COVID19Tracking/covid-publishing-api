"""This is where we defined the Config files, which are used for initiating the
application with specific settings such as logger configurations or different
database setups."""

from app.utils.logging import file_logger, client_logger
from decouple import config as env_conf
import logging
import testing.postgresql

class TestingPostgresqlConfig:
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # TODO(asilverstein): I think we need to figure out how to shut
        # this down cleanly.
        return testing.postgresql.Postgresql().url()

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    @staticmethod
    def init_app(app):
        pass

class LocalPSQLConfig:
    # To initate the local config. Basically adds bunch of logger handlers with
    # a postgre sql setup

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        DB_USER = env_conf('DATABASE_USER')
        DB_PASSWORD = env_conf('DATABASE_PASS')
        DB_HOST = env_conf('DATABASE_HOST')
        DB_PORT = env_conf('DATABASE_PORT')
        DB_NAME = env_conf('DATABASE_NAME')
        return 'postgresql+psycopg2://{}:{}@{}:{}/{}'.\
            format(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    SECRET_KEY = env_conf("SECRET_KEY", cast=str, default="12345")

    @staticmethod
    def init_app(app):
        # The default Flask logger level is set at ERROR, so if you want to see
        # INFO level or DEBUG level logs, you need to lower the main loggers
        # level first.
        app.logger.setLevel(logging.DEBUG)
        app.logger.addHandler(file_logger)
        app.logger.addHandler(client_logger)
        
class Testing:
    """Configuration for running the test suite"""
    
    TESTING = True
    DEBUG = True

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        DB_USER = env_conf('DATABASE_USER')
        DB_PASSWORD = env_conf('DATABASE_PASS')
        DB_HOST = env_conf('DATABASE_HOST')
        DB_PORT = env_conf('DATABASE_PORT')
        DB_NAME = env_conf('DATABASE_NAME')
        return 'postgresql+psycopg2://{}:{}@{}:{}/{}'.\
            format(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    SECRET_KEY = env_conf("SECRET_KEY", cast=str, default="12345")

    @staticmethod
    def init_app(app):
        # The default Flask logger level is set at ERROR, so if you want to see
        # INFO level or DEBUG level logs, you need to lower the main loggers
        # level first.
        app.logger.setLevel(logging.DEBUG)
        app.logger.addHandler(file_logger)
        app.logger.addHandler(client_logger)


class Develop:
    """Development config geared towards docker."""

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        DB_USER = "deploy"
        DB_PASSWORD = "docker"
        DB_HOST = "db"
        DB_PORT = "5432"
        DB_NAME = "stories"
        return 'postgresql+psycopg2://{}:{}@{}:{}/{}'.\
            format(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    # DEBUG = True
    # API configurations
    SECRET_KEY = env_conf("SECRET_KEY", cast=str, default="12345")

    @staticmethod
    def init_app(app):
        """Initiates application."""
        app.logger.setLevel(logging.DEBUG)
        app.logger.addHandler(client_logger)
        app.logger.addHandler(file_logger)


# Create a config dictionary which is used while initiating the application.
# Config that is going to be used will be specified in the .env file
config_dict = {
    'unittestpostgresql': TestingPostgresqlConfig,
    'localpsql': LocalPSQLConfig,
    'develop': Develop,
    'testing': Testing,
}
