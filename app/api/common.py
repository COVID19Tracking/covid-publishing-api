import flask
from flask import request

from app.models.data import *
from app import db

from sqlalchemy import func, and_
from sqlalchemy.sql import label


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

    if preview:
        filter_list.append(Batch.isPublished == False)
    else:
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