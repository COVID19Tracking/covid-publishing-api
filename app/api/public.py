"""Registers the necessary routes for the public API endpoints."""
import collections
from io import StringIO

import flask
from flask import request, make_response

from sqlalchemy import func, and_
from sqlalchemy.sql import label

from app.api import api
from app.api.common import states_daily_query, us_daily_query
from app.api.csvcommon import CSVColumn, make_csv_response
from app.models.data import *
from app import db

from flask_restful import inputs


@api.route('/public/states/info', methods=['GET'])
def get_states():
    states = State.query.all()
    return flask.jsonify(
        [state.to_dict() for state in states]
    )

@api.route('/public/states/info.csv', methods=['GET'])
def get_states_csv():
    states = State.query.order_by(State.state.asc()).all()
    columns = [CSVColumn(label="State", model_column="state"),
               CSVColumn(label="COVID-19 site", model_column="covid19Site"),
               CSVColumn(label="COVID-19 site (secondary)", model_column="covid19SiteSecondary"),
               CSVColumn(label="COVID-19 site (tertiary)", model_column="covid19SiteTertiary"),
               CSVColumn(label="Twitter", model_column="twitter"),
               CSVColumn(label="Notes", model_column="notes")]

    return make_csv_response(columns, states)

@api.route('/public/states/daily', methods=['GET'])
def get_states_daily():
    flask.current_app.logger.info('Retrieving States Daily')
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    latest_daily_data = states_daily_query(preview=include_preview).all()
    return flask.jsonify([x.to_dict() for x in latest_daily_data])

@api.route('/public/states/daily.csv', methods=['GET'])
def get_states_daily_csv():
    flask.current_app.logger.info('Retrieving States Daily')
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    latest_daily_data = states_daily_query(preview=include_preview).all()

    # rewrite date to %Y%m%d format to match the old public sheet
    reformatted_data = []
    for data in latest_daily_data:
        result_dict = data.to_dict()
        result_dict.update({
            'date': data.date.strftime("%Y%m%d"),
        })
        reformatted_data.append(result_dict)

    columns = [CSVColumn(label="Date", model_column="date"),
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
               CSVColumn(label="Deaths", model_column="death"),
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
               CSVColumn(label="Total Test Encounters (PCR)", model_column="totalTestEncountersViral"),
               CSVColumn(label="Total Antibody Tests (People)", model_column="totalTestsPeopleAntibody"),
               CSVColumn(label="Positive Antibody Tests (People)", model_column="positiveTestsPeopleAntibody"),
               CSVColumn(label="Negative Antibody Tests (People)", model_column="negativeTestsPeopleAntibody"),
               CSVColumn(label="Total Antigen Tests (People)", model_column="totalTestsPeopleAntigen"),
               CSVColumn(label="Positive Antigen Tests (People)", model_column="positiveTestsPeopleAntigen"),
               CSVColumn(label="Total Antigen Tests", model_column="totalTestsAntigen"),
               CSVColumn(label="Positive Antigen Tests", model_column="positiveTestsAntigen")
               ]

    return make_csv_response(columns, reformatted_data)

@api.route('/public/states/<string:state>/daily', methods=['GET'])
def get_states_daily_for_state(state):
    flask.current_app.logger.info('Retrieving States Daily for state %s' % state)
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    latest_daily_data_for_state = states_daily_query(
        state=state.upper(), preview=include_preview).all()
    if len(latest_daily_data_for_state) == 0:
        # likely state not found
        return flask.Response("States Daily data unavailable for state %s" % state, status=404)

    return flask.jsonify([x.to_dict() for x in latest_daily_data_for_state])


@api.route('/public/us/daily', methods=['GET'])
def get_us_daily():
    flask.current_app.logger.info('Retrieving US Daily')
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    us_data_by_date = us_daily_query(preview=include_preview)

    return flask.jsonify(us_data_by_date)

@api.route('/public/us/daily.csv', methods=['GET'])
def get_us_daily_csv():
    flask.current_app.logger.info('Retrieving US Daily')
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    us_data_by_date = us_daily_query(preview=include_preview, date_format="%Y%m%d")

    columns = [CSVColumn(label="Date", model_column="date"),
               CSVColumn(label="States", model_column="states"),
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
               CSVColumn(label="Deaths", model_column="death")]

    return make_csv_response(columns, us_data_by_date)