import csv
from datetime import timedelta
from io import StringIO

import flask
from dateutil import tz
from flask import make_response, request
from flask_restful import inputs

from app.api import api
from app.api.common import us_daily_query, states_daily_query
from app.api.csv_columns import CSVColumn, select, \
    STATES_CURRENT, STATES_DAILY, US_CURRENT_COLUMNS, US_DAILY_COLUMNS
from app.models.data import State, CoreData

"""Represents the recipe to generate a column of CSV output data.

This maps a model column name to a CSV column name. An ordered list of CSVColumns can be passed to `make_csv_response`
to generate CSV output
Example: ``CSVColumn(label="State", model_column="state")``

Columns that have ``blank=True`` will always be blank in the CSV output, used for deprecated columns
Example: ``CSVColumn(label="State", model_column=None, blank=True)``
"""


def make_csv_response(columns, data):
    """Generate a Flask response containing CSV data from `data` using the column definitions in ``columns``

    Outputs a header row, containing each column identified by the column's label in the order provided, followed by
    one line for each ``data`` row.

    Args:
        columns: A list of `CSVColumn` definitions. The output will contain each column in the given order
        data: SQLAlchemy query results or a dict to be output in CSV format

    Returns: Flask response in ``text/csv`` format
    """
    si = StringIO()
    writer = csv.writer(si)

    # write a header row
    writer.writerow([column.label for column in columns])

    # data may come in the form of sqlalchemy query results or a dict
    def get_data(datum, key, blank):
        if blank is True:
            return ""
        if isinstance(datum, dict):
            return datum.get(key)
        else:
            return datum.__getattribute__(key)

    # write data rows
    for datum in data:
        writer.writerow([get_data(datum, column.model_column, column.blank) for column in columns])
    output = make_response(si.getvalue())
    output.headers["Content-type"] = "text/csv"

    return output


@api.route('/v1/public/states/info.csv', methods=['GET'])
def get_states_csv():
    states = State.query.order_by(State.state.asc()).all()
    columns = [CSVColumn(label="State", model_column="state"),
               CSVColumn(label="COVID-19 site", model_column="covid19Site"),
               CSVColumn(label="COVID-19 site (secondary)", model_column="covid19SiteSecondary"),
               CSVColumn(label="COVID-19 site (tertiary)", model_column="covid19SiteTertiary"),
               CSVColumn(label="COVID-19 site (quaternary)", model_column="covid19SiteQuaternary"),
               CSVColumn(label="COVID-19 site (quinary)", model_column="covid19SiteQuinary"),
               CSVColumn(label="Twitter", model_column="twitter"),
               CSVColumn(label="Notes", model_column="notes"),
               CSVColumn(label="COVID Tracking Project preferred total test units",
                         model_column="covidTrackingProjectPreferredTotalTestUnits"),
               CSVColumn(label="COVID Tracking Project preferred total test field",
                         model_column="covidTrackingProjectPreferredTotalTestField")]

    return make_csv_response(columns, states)


def get_states_daily_data(preview, limit):
    latest_daily_data = states_daily_query(preview=preview, limit=limit).all()

    # rewrite date formats to match the old public sheet
    reformatted_data = []
    eastern_time = tz.gettz('EST')
    for data in latest_daily_data:
        result_dict = data.to_dict()
        result_dict.update({
            'date': data.date.strftime("%Y%m%d"),
            # due to DST issues, this time needs to be advanced forward one hour to match the old output
            'dateChecked': (data.dateChecked.astimezone(eastern_time) + timedelta(hours=1)).strftime(
                "%-m/%d/%Y %H:%M") if data.dateChecked else ""
        })

        # add the row to the output
        reformatted_data.append(result_dict)
    return reformatted_data


@api.route('/v1/internal/states/daily.csv', methods=['GET'], endpoint='states_latest')
def get_latest_states_daily_csv():
    preview = request.args.get('preview', default=False, type=inputs.boolean)
    days = request.args.get('days', default=1, type=inputs.positive)
    flask.current_app.logger.info('Retrieving US daily for {} days with preview = {}'.format(
        days, preview))

    states_data = get_states_daily_data(preview, limit=days)

    # need to return all columns, with their db names
    columns = [CSVColumn(label=c.name, model_column=c.name) for c in CoreData.__table__.columns]
    return make_csv_response(columns, states_data)


@api.route('/v1/public/states/daily.csv', methods=['GET'], endpoint='states_daily')
@api.route('/v1/public/states/current.csv', methods=['GET'], endpoint='states_current')
def get_states_daily_csv():
    flask.current_app.logger.info('Retrieving States Daily')
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)

    limit = None
    if request.endpoint == 'api.states_current':
        limit = 1
    states_data = get_states_daily_data(include_preview, limit)

    columns = STATES_CURRENT
    if request.endpoint == 'api.states_daily':
        columns = STATES_DAILY
    columns = select(columns)

    return make_csv_response(columns, states_data)


@api.route('/v1/public/us/daily.csv', methods=['GET'], endpoint='us_daily')
@api.route('/v1/public/us/current.csv', methods=['GET'], endpoint='us_current')
def get_us_daily_csv():
    flask.current_app.logger.info('Retrieving US Daily')
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    limit = 1 if request.endpoint == 'api.us_current' else None
    us_data_by_date = us_daily_query(preview=include_preview, date_format="%Y%m%d", limit=limit)

    columns = US_CURRENT_COLUMNS
    if request.endpoint == 'api.us_daily':
        columns = US_DAILY_COLUMNS
    columns = select(columns)
    return make_csv_response(columns, us_data_by_date)
