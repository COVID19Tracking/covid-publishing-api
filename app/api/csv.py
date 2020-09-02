import collections
import csv
from datetime import timedelta
from io import StringIO

import flask
from dateutil import tz
from flask import make_response, request
from flask_restful import inputs

from app.api import api
from app.api.common import us_daily_query, states_daily_query, State

CSVColumn = collections.namedtuple('Column', 'label model_column blank')
CSVColumn.__new__.__defaults__ = (False, )
"""Represents the recipe to generate a column of CSV output data. 

This maps a model column name to a CSV column name. An ordered list of CSVColumns can be passed to `make_csv_response`
to generate CSV output
Example: ``CSVColumn(label="State", model_column="state")``
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


@api.route('/public/states/info.csv', methods=['GET'])
def get_states_csv():
    states = State.query.order_by(State.state.asc()).all()
    columns = [CSVColumn(label="State", model_column="state"),
               CSVColumn(label="COVID-19 site", model_column="covid19Site"),
               CSVColumn(label="COVID-19 site (secondary)", model_column="covid19SiteSecondary"),
               CSVColumn(label="COVID-19 site (tertiary)", model_column="covid19SiteTertiary"),
               CSVColumn(label="Twitter", model_column="twitter"),
               CSVColumn(label="Notes", model_column="notes"),
               CSVColumn(label="COVID Tracking Project preferred total test units",
                         model_column="covidTrackingProjectPreferredTotalTestUnits"),
               CSVColumn(label="COVID Tracking Project preferred total test field",
                         model_column="covidTrackingProjectPreferredTotalTestField")]

    return make_csv_response(columns, states)


@api.route('/public/states/daily.csv', methods=['GET'], endpoint='states_daily')
@api.route('/public/states/current.csv', methods=['GET'], endpoint='states_current')
def get_states_daily_csv():
    flask.current_app.logger.info('Retrieving States Daily')
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    latest_daily_data = states_daily_query(preview=include_preview).all()

    # rewrite date formats to match the old public sheet
    reformatted_data = []
    state_latest_dates = {}
    eastern_time = tz.gettz('EST')
    for data in latest_daily_data:
        result_dict = data.to_dict()
        result_dict.update({
            'date': data.date.strftime("%Y%m%d"),
            # due to DST issues, this time needs to be advanced forward one hour to match the old output
            'dateChecked': (data.dateChecked.astimezone(eastern_time) + timedelta(hours=1)).strftime(
                "%-m/%d/%Y %H:%M") if data.dateChecked else ""
        })

        # for the /current endpoint, only add the row if it's the latest data for the state
        if request.endpoint == 'api.states_current':
            # if we've seen this state before and the one we saw is newer, skip this row
            if data.state in state_latest_dates and state_latest_dates[data.state] > data.date:
                continue
            state_latest_dates[data.state] = data.date

        # add the row to the output
        reformatted_data.append(result_dict)

    columns = []

    if request.endpoint != 'api.states_current':
        columns.append(CSVColumn(label="Date", model_column="date"))

    columns.extend([
        CSVColumn(label="State", model_column="state"),
        CSVColumn(label="Positive", model_column="positive"),
        CSVColumn(label="Negative", model_column="negative"),
        CSVColumn(label="Pending", model_column="pending"),
        CSVColumn(label="Hospitalized – Currently", model_column="hospitalizedCurrently"),
        CSVColumn(label="Hospitalized – Cumulative", model_column="hospitalizedCumulative"),
        CSVColumn(label="In ICU – Currently", model_column="inIcuCurrently"),
        CSVColumn(label="In ICU – Cumulative", model_column="inIcuCumulative"),
        CSVColumn(label="On Ventilator – Currently", model_column="onVentilatorCurrently"),
        CSVColumn(label="On Ventilator – Cumulative", model_column="onVentilatorCumulative"),
        CSVColumn(label="Recovered", model_column="recovered"),
        CSVColumn(label="Deaths", model_column="death")])

    if request.endpoint == 'api.states_current':
        columns.extend([
            CSVColumn(label="Last Update ET", model_column="lastUpdateEt"),
            CSVColumn(label="Check Time (ET)", model_column="dateChecked")])
    else:
        columns.extend([
            CSVColumn(label="Data Quality Grade", model_column="dataQualityGrade"),
            CSVColumn(label="Last Update ET", model_column="lastUpdateEt"),
            CSVColumn(label="Total Antibody Tests", model_column="totalTestsAntibody"),
            CSVColumn(label="Positive Antibody Tests", model_column="positiveTestsAntibody"),
            CSVColumn(label="Negative Antibody Tests", model_column="negativeTestsAntibody"),
            CSVColumn(label="Total Tests (PCR)", model_column="totalTestsViral"),
            CSVColumn(label="Positive Tests (PCR)", model_column="positiveTestsViral"),
            CSVColumn(label="Negative Tests (PCR)", model_column="negativeTestsViral"),
            CSVColumn(label="Positive Cases (PCR)", model_column="positiveCasesViral"),
            CSVColumn(label="Deaths (confirmed)", model_column="deathConfirmed"),
            CSVColumn(label="Deaths (probable)", model_column="deathProbable"),
            CSVColumn(label="Total PCR Tests (People)", model_column="totalTestsPeopleViral"),
            CSVColumn(label="Total Test Results", model_column=None, blank=True),
            CSVColumn(label="Probable Cases", model_column="probableCases"),
            CSVColumn(label="Total Test Encounters (PCR)", model_column="totalTestEncountersViral"),
            CSVColumn(label="Total Antibody Tests (People)", model_column="totalTestsPeopleAntibody"),
            CSVColumn(label="Positive Antibody Tests (People)", model_column="positiveTestsPeopleAntibody"),
            CSVColumn(label="Negative Antibody Tests (People)", model_column="negativeTestsPeopleAntibody"),
            CSVColumn(label="Total Antigen Tests (People)", model_column="totalTestsPeopleAntigen"),
            CSVColumn(label="Positive Antigen Tests (People)", model_column="positiveTestsPeopleAntigen"),
            CSVColumn(label="Negative Antigen Tests (People)", model_column="negativeTestsPeopleAntigen"),
            CSVColumn(label="Total Antigen Tests", model_column="totalTestsAntigen"),
            CSVColumn(label="Positive Antigen Tests", model_column="positiveTestsAntigen"),
            CSVColumn(label="Negative Antigen Tests", model_column="negativeTestsAntigen")])

    return make_csv_response(columns, reformatted_data)


@api.route('/public/us/daily.csv', methods=['GET'], endpoint='us_daily')
@api.route('/public/us/current.csv', methods=['GET'], endpoint='us_current')
def get_us_daily_csv():
    flask.current_app.logger.info('Retrieving US Daily')
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    us_data_by_date = us_daily_query(preview=include_preview, date_format="%Y%m%d")

    # the /current endpoint only returns the latest data instead of all dates
    # and is missing the Date and States columns
    if request.endpoint == 'api.us_current':
        us_data_by_date = us_data_by_date[:1]

    columns = []

    if request.endpoint != 'api.us_current':
        columns.extend([CSVColumn(label="Date", model_column="date"),
                        CSVColumn(label="States", model_column="states")])

    columns.extend([
        CSVColumn(label="Positive", model_column="positive"),
        CSVColumn(label="Negative", model_column="negative"),
        CSVColumn(label="Pending", model_column="pending"),
        CSVColumn(label="Hospitalized – Currently", model_column="hospitalizedCurrently"),
        CSVColumn(label="Hospitalized – Cumulative", model_column="hospitalizedCumulative"),
        CSVColumn(label="In ICU – Currently", model_column="inIcuCurrently"),
        CSVColumn(label="In ICU – Cumulative", model_column="inIcuCumulative"),
        CSVColumn(label="On Ventilator – Currently", model_column="onVentilatorCurrently"),
        CSVColumn(label="On Ventilator – Cumulative", model_column="onVentilatorCumulative"),
        CSVColumn(label="Recovered", model_column="recovered"),
        CSVColumn(label="Deaths", model_column="death")])

    return make_csv_response(columns, us_data_by_date)
