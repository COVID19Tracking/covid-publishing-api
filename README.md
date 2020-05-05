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
export FLASK_APP=stories.py
flask run
```

This will start a local server at http://127.0.0.1:5000/. For now, the landing index.html uses the template Stories SQLAlchemy model, so this link won't work if you're connected to the CTP data DB.

Instead, to test just API routing, you can go to: http://127.0.0.1:5000/api/v1/test/
To test your CTP DB connection and list a bunch of batch IDs, go to: http://127.0.0.1:5000/api/v1/data/batch/

## Running data_convert

Data Convert is a standalone Python module that gets data from the google sheet and converts it into a
typed and filtered Pandas DataFrame based on a meta-data file.  

To view the JSON for the current worksheet under development, run
    > python tab_working.py
To view the JSON for the Checks tab, run
    > python tab_checks.py

## Running the tests

The project contains a tests directory that uses pytest.  

For it to work, the root file of the repo needs be accessible as a Python module.  The easiest way to do this is:
    > cd tests
    > export PYTHONPATH=<base path for the repo>
    > pytests

All tests are run automatically by CircleCI when you create a PR that connects to master.  Please make
sure tests run relatively quickly (seconds, not minutes).

## Documents

Design Doc (https://docs.google.com/document/d/16JVr3aQE18BUEgrjf7UwQ7ssgghrYqN0lnCjzkghLV0/edit#heading=h.ng2qoy23i2hp)

Data Entry Sheet (https://docs.google.com/spreadsheets/d/1MvvbHfnjF67GnYUDJJiNYUmGco5KQ9PW0ZRnEP9ndlU/edit#gid=2335020)
