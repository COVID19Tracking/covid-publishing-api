"""Registers the necessary routes for the public API endpoints."""

from flask import jsonify, request, current_app, abort
from sqlalchemy import func, and_
from sqlalchemy.sql import label

from app.api import api
from app.models.data import *
from app import db


@api.route('/public/states/info', methods=['GET'])
def get_states():
    states = State.query.all()
    return jsonify(
        [state.to_dict() for state in states]
    )


# grabbed this solution from:
# https://stackoverflow.com/questions/45775724/sqlalchemy-group-by-and-return-max-date?rq=1
#
# Returns a SQLAlchemy BaseQuery object
def states_daily_query():
    # first retrieve latest published batch per state
    latest_state_daily_batches = db.session.query(
        CoreData.state, CoreData.date, func.max(CoreData.batchId).label('maxBid')
        ).join(Batch).filter(Batch.dataEntryType=='daily').filter(Batch.isPublished==True
        ).group_by(CoreData.state, CoreData.date
        ).subquery('latest_state_daily_batches')

    latest_daily_data_query = db.session.query(CoreData).join(
        latest_state_daily_batches,
        and_(
            CoreData.batchId == latest_state_daily_batches.c.maxBid,
            CoreData.state == latest_state_daily_batches.c.state,
            CoreData.date == latest_state_daily_batches.c.date
        ))

    return latest_daily_data_query


@api.route('/public/states/daily', methods=['GET'])
def get_states_daily():
    current_app.logger.info('Retrieving States Daily')
    latest_daily_data = states_daily_query().all()
    return jsonify([x.to_dict() for x in latest_daily_data])


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
    current_app.logger.info('Retrieving US Daily')
    states_daily = states_daily_query().subquery('states_daily')

    # get a list of columns to aggregate, sum over those from the states_daily subquery
    colnames = get_us_daily_column_names()
    col_list = [label(colname, func.sum(getattr(states_daily.c, colname))) for colname in colnames]
    us_daily = db.session.query(states_daily.c.date, *col_list).group_by(states_daily.c.date).all()

    us_data_by_date = []
    for day in us_daily:
        result_dict = day._asdict()
        # TODO: add the number of states
        result_dict.update({
            'dateChecked': day.date.isoformat(),
            'date': day.date.strftime('%Y%m%d'),
        })
        us_data_by_date.append(result_dict)

    return jsonify(us_data_by_date)

