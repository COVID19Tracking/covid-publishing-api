"""This file is the main module which contains the app.
"""
from app import create_app, db
from app.auth.auth_cli import getToken
from decouple import config
from flask.cli import AppGroup
import click

import config as configs

# Figure out which config we want based on the `ENV` env variable, default to local
env_config = config("ENV", cast=str, default="localpsql")
config_dict = {
    'production': configs.Production,
    'localpsql': configs.LocalPSQLConfig,
    'develop': configs.Develop,
    'testing': configs.Testing,
}

app = create_app(config_dict[env_config]())

# for production, require a real SECRET_KEY to be set
if env_config == 'production':
    assert app.config['SECRET_KEY'] != "12345", "You must set a secure SECRET_KEY"

# register a custom command to get authentication tokens
auth_cli = AppGroup('auth')
@auth_cli.command("getToken")
@click.argument('name')
def getToken_cli(name):
   click.echo(getToken(name))
   
app.cli.add_command(auth_cli)

@app.cli.command()
def deploy():
    """Run deployment tasks"""
    # e.g. this _used_ to be where a database migration would run via `upgrade()`
    pass
