"""This file is the main module which contains the app, where all the good
stuff happens. You will always want to point your applications like Gunicorn
to this file, which will pick up the app to run their servers.
"""
from app import create_app, db
from app.auth.auth_cli import getToken
from decouple import config
from flask.cli import AppGroup
import click

import config as configs

# Figure out which config we want based on the `ENV` env variable
env_config = config("ENV", cast=str, default="develop")
config_dict = {
    'localpsql': configs.LocalPSQLConfig,
    'develop': configs.Develop,
    'testing': configs.Testing,
}

app = create_app(config_dict[env_config]())

# More custom commands can be added to flasks CLI here(for running tests and
# other stuff)

# register a custom command to get authenticaiton tokens
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
