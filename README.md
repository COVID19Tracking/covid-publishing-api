# Database backed API

This repo will (eventually) implement an API that sits between the data entry spreadsheet and the public web site.  Internally, it records data to a relational database.

Briefly, this is a Flask + SQLAlchemy app that manages communication with the database. The implementation is based on the template from https://github.com/alisezer/flask-template. Please see the README in that project for more details on the setup.

## Development

This project assumes you have Python 3.6. You can use `pip install -r requirements.txt` to get dependencies, but it's recommended to use Conda (more container friendly later) to create the environment with all dependencies (see `environment.yml`):
```shell
conda env create --file environment.yml
```

To run the application once you create the environment, you need to make an .env file from the included template:
```shell
cp .env.template .env
```

You'll need to edit the database configuration variables in the .env file to use the models. This can work either with your local DB install or you can connect to a remote PostgreSQL instance.

## Running the app

Assuming you've done the DB setup, you can run like this (for now using the original template files):
```shell
export FLASK_APP=flask_server.py
flask run
```

This will start a local server at http://127.0.0.1:5000/. For now, the landing index.html uses the template Stories SQLAlchemy model, so this link won't work if you're connected to the CTP data DB.

Instead, to test just API routing, you can go to: http://127.0.0.1:5000/api/v1/test/
To test your CTP DB connection and list a bunch of batch IDs, go to: http://127.0.0.1:5000/api/v1/data/batch/

Finally, to spin up a whole stack using docker:
```
docker build -t cvapi .
docker run -it -p 8000:8000 cvapi
```
This is a WIP, but asilverstein@ would like this to be a part of the normal testing flow.

## DB setup/migration

This repo has been set up with Alembic migrations through Flask, using `flask init db`. If you're getting started in a development environment and you make a model change that needs a migration, do the following once you update the model code:
```shell
flask db migrate -m 'Describe your migration'
```
This will make Alembic generate a new file under migrations/versions. The migration is applied to the database specified in your environment by running:
```shell
flask db upgrade
```

## Running the tests

The project contains a tests directory that uses pytest.  

You can run the tests with `python -m pytest` once your environemnt is configured

All tests are run automatically by CircleCI when you create a PR that connects to master.  Please make
sure tests run relatively quickly (seconds, not minutes).

## Documents

Design Doc (https://docs.google.com/document/d/16JVr3aQE18BUEgrjf7UwQ7ssgghrYqN0lnCjzkghLV0/edit#heading=h.ng2qoy23i2hp)

Data Entry Sheet (https://docs.google.com/spreadsheets/d/1MvvbHfnjF67GnYUDJJiNYUmGco5KQ9PW0ZRnEP9ndlU/edit#gid=2335020)
