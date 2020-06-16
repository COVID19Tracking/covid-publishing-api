"""Registers the necessary routes for the public API endpoints."""

import flask
from flask import request

from sqlalchemy import func, and_
from sqlalchemy.sql import label

from app.api import api
from app.models.data import *
from app import db

from flask_restful import inputs

@api.route('/public/states/info', methods=['GET'])
def get_states():
    states = State.query.all()
    return flask.jsonify(
        [state.to_dict() for state in states]
    )


# grabbed this solution from:
# https://stackoverflow.com/questions/45775724/sqlalchemy-group-by-and-return-max-date?rq=1
#
# Returns a SQLAlchemy BaseQuery object. If input state is not None, will return daily data only
# for the input state.
def states_daily_query(state=None, preview=False):
    # first retrieve latest published batch per state
    filter_list = [Batch.dataEntryType.in_(['daily', 'edit'])]
    if state is not None:
        filter_list.append(CoreData.state == state)
    if not preview:
        filter_list.append(Batch.isPublished == True)

    latest_state_daily_batches = db.session.query(
        CoreData.state, CoreData.date, func.max(CoreData.batchId).label('maxBid')
        ).join(Batch
        ).filter(*filter_list
        ).group_by(CoreData.state, CoreData.date
        ).subquery('latest_state_daily_batches')

    latest_daily_data_query = db.session.query(CoreData).join(
        latest_state_daily_batches,
        and_(
            CoreData.batchId == latest_state_daily_batches.c.maxBid,
            CoreData.state == latest_state_daily_batches.c.state,
            CoreData.date == latest_state_daily_batches.c.date
        )).order_by(CoreData.date.desc()
        ).order_by(CoreData.state)

    return latest_daily_data_query


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
    latest_daily_data_for_state = states_daily_query(state=state.upper(), preview=include_preview).all()
    if len(latest_daily_data_for_state) == 0:
        # likely state not found
        return flask.Response("States Daily data unavailable for state %s" % state, status=404)

    return flask.jsonify([x.to_dict() for x in latest_daily_data_for_state])


# Returns a list of CoreData column names representing numerical data that needs to be summed and
# served in States Daily.
def get_us_daily_column_names():
    colnames = []
    for column in CoreData.__table__.columns:
        if column.info.get("includeInUSDaily") == True:
            colnames.append(column.name)

    return colnames


@api.route('/public/us/daily', methods=['GET'])
def get_us_daily():
    flask.current_app.logger.info('Retrieving US Daily')
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    states_daily = states_daily_query(preview=include_preview).subquery('states_daily')

    # get a list of columns to aggregate, sum over those from the states_daily subquery
    colnames = get_us_daily_column_names()
    col_list = [label(colname, func.sum(getattr(states_daily.c, colname))) for colname in colnames]
    # Add a column to count the records contributing to this date. That should
    # correspond to the number of states, assuming `states_daily` returns
    # only a single row per state.
    col_list.append(label('states', func.count()))
    us_daily = db.session.query(
        states_daily.c.date, *col_list
        ).group_by(states_daily.c.date
        ).order_by(states_daily.c.date.desc()
        ).all()

    us_data_by_date = []
    for day in us_daily:
        result_dict = day._asdict()
        result_dict.update({
            'dateChecked': day.date.isoformat(),
            'date': day.date.strftime('%Y%m%d'),
        })
        us_data_by_date.append(result_dict)

    return flask.jsonify(us_data_by_date)
