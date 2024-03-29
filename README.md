**As of March 7, 2021 we are [no longer collecting new data](https://covidtracking.com/analysis-updates/giving-thanks-and-looking-ahead-our-data-collection-work-is-done). [Learn about available federal data](https://covidtracking.com/analysis-updates/federal-covid-data-101-how-to-find-data).**

---

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
This will make Alembic generate a new file under migrations/versions.

EXTREMELY IMPORTANT: Flask-Migrate (and Alembic's `autogenerate` which backs it) does not automatically detect renamed columns, instead turning them into a column deletion and a column addition. See [Alembic's docs](https://alembic.sqlalchemy.org/en/latest/autogenerate.html#what-does-autogenerate-detect-and-what-does-it-not-detect) for more details on what will be auto-detected. If you're creating a migration, you _must_ open it up and confirm that, unless you're completely sure you intended to delete a column, there are no `drop_column` instances. e.g. [this is bad](https://github.com/COVID19Tracking/covid-publishing-api/commit/bfe649e9c0bde36910ba3719be304d22e2f29f74), [this is good](https://github.com/COVID19Tracking/covid-publishing-api/commit/555b731920cb02395d382a6cfc676887d4954a0d).

Once you're happy with the migration and someone else has signed off on it, you can apply it to the database specified in your environment by running:
```shell
flask db upgrade
```

## Running the tests

The project contains a tests directory that uses pytest.  

You can run the tests with `python -m pytest` once your environemnt is configured

All tests are run automatically by CircleCI when you create a PR that connects to master.  Please make
sure tests run relatively quickly (seconds, not minutes).

## Authentication

Endpoints that create/update data are authenticated with a JWT bearer token. 

To obtain a token, run:
```shell
flask auth getToken tokenName
```

The token is secured by the value of `SECRET_KEY`, so tokens generated in one environment will not work elsewhere 
unless they have the same secret (this value should overridden on any server).

To pass a token to the API, include it as a header:
```
Authorization: Bearer <token>
```

When writing tests that call authenticated endpoints, use the `headers` fixture to obtain a headers object containing a valid token.
When writing endpoints that require authentication, use the `@jwt_required` decorator.

## Documents

Design Doc (https://docs.google.com/document/d/16JVr3aQE18BUEgrjf7UwQ7ssgghrYqN0lnCjzkghLV0/edit#heading=h.ng2qoy23i2hp)

Data Entry Sheet (https://docs.google.com/spreadsheets/d/1MvvbHfnjF67GnYUDJJiNYUmGco5KQ9PW0ZRnEP9ndlU/edit#gid=2335020)
