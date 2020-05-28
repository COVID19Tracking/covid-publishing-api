"""Registers the necessary routes for the public API endpoints."""

from flask import jsonify, request, current_app, abort
from app.api import api
from app.models.data import *
from app import db

from sqlalchemy import func, and_

##############################################################################################
######################################   States      #########################################
##############################################################################################

@api.route('/public/states/info', methods=['GET'])
def get_states():
    states = State.query.all()
    return jsonify(
        [state.to_dict() for state in states]
    )

# grabbed this solution from:
# https://stackoverflow.com/questions/45775724/sqlalchemy-group-by-and-return-max-date?rq=1
@api.route('/public/states/daily', methods=['GET'])
def get_states_daily():
    current_app.logger.info('Retrieving States Daily')
    # first retrieve latest published batch per state
    latest_state_daily_batches = db.session.query(
        CoreData.state, CoreData.date, func.max(CoreData.batchId).label('maxBid')
        ).join(Batch).filter(Batch.dataEntryType=='daily').filter(Batch.isPublished==True
        ).group_by(CoreData.state, CoreData.date
        ).subquery('latest_state_daily_batches')

    latest_daily_data = db.session.query(CoreData).join(
        latest_state_daily_batches,
        and_(
            CoreData.batchId == latest_state_daily_batches.c.maxBid,
            CoreData.state == latest_state_daily_batches.c.state,
            CoreData.date == latest_state_daily_batches.c.date
        )).all()

    return jsonify([x.to_dict() for x in latest_daily_data])
