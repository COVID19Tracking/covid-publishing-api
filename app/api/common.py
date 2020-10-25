from collections import defaultdict

from app.models.data import CoreData, Batch
from app import db

from sqlalchemy import func, and_
from sqlalchemy.sql import label


# grabbed this solution from:
# https://stackoverflow.com/questions/45775724/sqlalchemy-group-by-and-return-max-date?rq=1
#
# Returns a SQLAlchemy BaseQuery object. If input state is not None, will return daily data only
# for the input state.
def states_daily_query(state=None, preview=False, limit=None):
    # first retrieve latest published batch per state
    filter_list = [Batch.dataEntryType.in_(['daily', 'edit'])]
    if state is not None:
        if isinstance(state, str):
            state = [state]
        filter_list.append(CoreData.state.in_(state))

    if preview:
        filter_list.append(Batch.isPublished == False)
    else:
        filter_list.append(Batch.isPublished == True)

    # The query here uses a window function using over/partition-by, the specific window
    # function that's used is row_number, because we want at most $limit number of
    # newest rows for each state. So we partition by state and order by date desc, assing
    # row_number, and then filter by this row number
    latest_state_daily_batches = db.session.query(
        CoreData.state, CoreData.date, func.max(CoreData.batchId).label('maxBid'),
        func.row_number().over(
            partition_by=CoreData.state, order_by=CoreData.date.desc()).label('row')
    ).join(Batch).filter(*filter_list).group_by(
        CoreData.date, CoreData.state
    ).order_by(CoreData.date.desc(), CoreData.state).subquery('latest_state_daily_batches')

    filter_list = []
    if limit is not None:
        filter_list = [latest_state_daily_batches.c.row <= limit]

    latest_daily_data_query = db.session.query(CoreData).join(
        latest_state_daily_batches,
        and_(
            CoreData.batchId == latest_state_daily_batches.c.maxBid,
            CoreData.state == latest_state_daily_batches.c.state,
            CoreData.date == latest_state_daily_batches.c.date
        )).filter(*filter_list).order_by(CoreData.date.desc()).order_by(CoreData.state)

    return latest_daily_data_query


def us_daily_query(preview=False, date_format='%Y-%m-%d', limit=None):
    """Query US Daily Data

    Sums up the numeric columns from the data for all states to provide an aggregate for the whole
    country.

    Args:
        preview (bool, optional): return data in the preview state or only published data. Optional,
            defaults to False
        date_format: (str, optional): optional strftime format string.
            If provided, the `date` property of the output will be formatted in the specified
            fashion (default '%Y-%m-%d')

    Returns:
        dict: Dictionary of US daily data, one row per date
    """
    states_daily = states_daily_query(preview=preview, limit=limit).subquery('states_daily')

    # get a list of columns to aggregate, sum over those from the states_daily subquery
    colnames = CoreData.numeric_fields()
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

    # short term hack: we need to get totalTestResults as an aggregate, but since it's a hybrid
    # property, this is difficult without complex sql. Instead, getting states daily results as
    # CoreData objects, and going to do aggregation in Python.
    date_total_results_dict = defaultdict(int)
    states_daily_full_results = states_daily_query(preview=preview).all()
    for result in states_daily_full_results:
        if result.totalTestResults is not None:
            date_total_results_dict[result.date] += result.totalTestResults

    us_data_by_date = []
    for day in us_daily:
        result_dict = day._asdict()
        # grab totalTestResults from the aggregation-by-date dict we just computed, and update
        # date object formats
        result_dict.update({
            'totalTestResults': date_total_results_dict[day.date],
            'dateChecked': day.date.isoformat(),
            'date': day.date.strftime(date_format),
        })
        us_data_by_date.append(result_dict)

    return us_data_by_date
