"""This is where we defined the Config files, which are used for initiating the
application with specific settings such as logger configurations or different
database setups."""

from app.utils.logging import file_logger, client_logger
from decouple import config as env_conf
import logging


# To use this config, set up a local Postgres server on 127.0.0.1 port 5432, make a database
# called "data", and create a user named "postgres" with no password and all privileges.
class LocalPSQLConfig:
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        DB_USER = 'postgres'
        DB_PASSWORD = ''
        DB_HOST = '127.0.0.1'
        DB_PORT = '5432'
        DB_NAME = 'data'
        return 'postgresql+psycopg2://{}:{}@{}:{}/{}'.\
            format(DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME)

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    SECRET_KEY = env_conf("SECRET_KEY", cast=str, default="12345")
    # by default, access tokens do not expire
    JWT_ACCESS_TOKEN_EXPIRES = env_conf('JWT_ACCESS_TOKEN_EXPIRES', cast=int, default=False)

    API_WEBHOOK_URL = env_conf('API_WEBHOOK_URL', cast=str, default=None)

    @staticmethod
    def init_app(app):
        # The default Flask logger level is set at ERROR, so if you want to see
        # INFO level or DEBUG level logs, you need to lower the main loggers
        # level first.
        app.logger.setLevel(logging.DEBUG)
        app.logger.addHandler(file_logger)
        app.logger.addHandler(client_logger)


class Production:
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
    # by default, access tokens do not expire
    JWT_ACCESS_TOKEN_EXPIRES = env_conf('JWT_ACCESS_TOKEN_EXPIRES', cast=int, default=False)

    API_WEBHOOK_URL = env_conf('API_WEBHOOK_URL', cast=str, default=None)

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
    # by default, access tokens do not expire
    JWT_ACCESS_TOKEN_EXPIRES = env_conf('JWT_ACCESS_TOKEN_EXPIRES', cast=int, default=False)

    API_WEBHOOK_URL = env_conf('API_WEBHOOK_URL', cast=str, default=None)

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

    API_WEBHOOK_URL = env_conf('API_WEBHOOK_URL', cast=str, default=None)

    # DEBUG = True
    # API configurations
    SECRET_KEY = env_conf("SECRET_KEY", cast=str, default="12345")
    # by default, access tokens do not expire
    JWT_ACCESS_TOKEN_EXPIRES = env_conf('JWT_ACCESS_TOKEN_EXPIRES', cast=int, default=False)

    @staticmethod
    def init_app(app):
        """Initiates application."""
        app.logger.setLevel(logging.DEBUG)
        app.logger.addHandler(client_logger)
        app.logger.addHandler(file_logger)
