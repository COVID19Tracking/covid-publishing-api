"""Registers the necessary routes for the public API endpoints."""

import flask
from flask import request
from flask_restful import inputs

from app.api import api
from app.api.common import states_daily_query, us_daily_query
from app.models.data import *


@api.route('/public/states/info', methods=['GET'])
def get_states():
    states = State.query.order_by(State.state.asc()).all()
    return flask.jsonify(
        [state.to_dict() for state in states]
    )


@api.route('/public/states/daily', methods=['GET'])
def get_states_daily():
    flask.current_app.logger.info('Retrieving States Daily')
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    latest_daily_data = states_daily_query(preview=include_preview).all()
    return flask.jsonify([x.to_dict() for x in latest_daily_data])


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
