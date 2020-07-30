"""This is where we create a function for initiating the application, which is
later on used at the very top level stories.py module to initiate the
application with a specific config file"""

# Flask Imports
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager

# For the database
db = SQLAlchemy()
migrate = Migrate()
bootstrap = Bootstrap()

def create_app(config):
    app = Flask(__name__)

    app.config.from_object(config)
    config.init_app(app)

    bootstrap.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    
    # setup flask_jwt_extended for authentication
    app.config['JWT_SECRET_KEY'] = app.config['SECRET_KEY']
    jwt = JWTManager(app)

    # Register our API blueprint
    from app.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1')

    # Register utils blueprint; this contains backfill logic
    from app.utils import utils as utils_blueprint
    app.register_blueprint(utils_blueprint)

    # register an error handler to return full exceptions for server errors
    @app.errorhandler(500)
    def internal_server_error(e):
        return str(e.original_exception), 500

    return app
