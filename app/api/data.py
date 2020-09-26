"""Registers the necessary routes for the core data model. """

from datetime import datetime

import flask
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func, and_

from app import db
from app.api import api
from app.api.common import states_daily_query
from app.models.data import Batch, CoreData, State
from app.utils.editdiff import EditDiff, ChangedValue, ChangedRow
from app.utils.slacknotifier import notify_slack, notify_slack_error, exceptions_to_slack
from app.utils.validation import validate_core_data_payload, validate_edit_data_payload
from app.utils.webhook import notify_webhook


##############################################################################################
######################################   Health check      ###################################
##############################################################################################


@api.route('/test', methods=['GET'])
def get_data():
    flask.current_app.logger.info('Retrieving all data: placeholder')
    flask.current_app.logger.debug('This is a debug log')
    return flask.jsonify({'test_data_key': 'test_data_value'})


@api.route('/test_auth', methods=['GET'])
@jwt_required
def test_auth():
    return flask.jsonify({'user': 'authenticated'}), 200

##############################################################################################
######################################   Batches      ########################################
##############################################################################################


@api.route('/batches', methods=['GET'])
def get_batches():
    flask.current_app.logger.info('Retrieving all batches')
    batches = Batch.query.all()
    # for each batch, attach its coreData rows

    return flask.jsonify({
        'batches': [batch.to_dict() for batch in batches]
    })


@api.route('/batches/<int:id>', methods=['GET'])
def get_batch_by_id(id):
    batch = Batch.query.get_or_404(id)
    flask.current_app.logger.info('Returning batch %d' % id)
    return flask.jsonify(batch.to_dict())


@api.route('/batches/<int:id>/publish', methods=['POST'])
@jwt_required
@notify_webhook
@exceptions_to_slack
def publish_batch(id):
    flask.current_app.logger.info('Received request to publish batch %d' % id)
    batch = Batch.query.get_or_404(id)

    # if batch is already published, fail out
    if batch.isPublished:
        return 'Batch %d already published, rejecting double-publish' % id, 422

    batch.isPublished = True
    batch.publishedAt = datetime.utcnow()   # set publish time to now
    db.session.add(batch)
    db.session.commit()

    notify_slack(f"*Published batch #{id}* (type: {batch.dataEntryType})\n"
                 f"{batch.batchNote}")

    return flask.jsonify(batch.to_dict()), 201


##############################################################################################
#######################################     States      ######################################
##############################################################################################


@api.route('/states/edit', methods=['POST'])
@jwt_required
@notify_webhook
@exceptions_to_slack
def edit_state_metadata():
    payload = flask.request.json
    flask.current_app.logger.info('Received a states edit request: %s' % payload)

    # we expect the payload to contain states
    if 'states' not in payload:
        err = '/states/edit payload must contain "states" field'
        flask.current_app.logger.error(err)
        notify_slack_error(err, 'edit_state_metadata')
        return err, 400

    state_dicts = payload['states']
    state_objects = []
    for state_dict in state_dicts:
        state_pk = state_dict['state']
        state_obj = db.session.query(State).get(state_pk)
        if state_obj is None:
            err = '/states/edit payload trying to edit nonexistent state: %s' % state_pk
            flask.current_app.logger.error(err)
            notify_slack_error(err, 'edit_state_metadata')
            return err, 400

        flask.current_app.logger.info('Updating state row from info: %s' % state_dict)
        db.session.query(State).filter_by(state=state_pk).update(state_dict)
        # this method of updating does not trigger validators, so validate manually
        state_obj.validate_totalTestResultsFieldDbColumn(None, state_obj.totalTestResultsFieldDbColumn)
        state_objects.append(db.session.query(State).get(state_pk))  # return updated state

    db.session.flush()

    # construct the JSON before committing the session, since sqlalchemy objects behave weirdly
    # once the session has been committed
    json_to_return = {
        'states': [state.to_dict() for state in state_objects],
    }

    db.session.commit()

    # this returns a tuple of flask response and status code: (flask.Response, int)
    return flask.jsonify(json_to_return), 201


##############################################################################################
######################################   Core data      ######################################
##############################################################################################

# Expects a dictionary of push context, state info, and core data rows. Writes to DB.
def post_core_data_json(payload):
    # test the input data
    try:
        validate_core_data_payload(payload)
    except ValueError as e:
        flask.current_app.logger.error('Data post failed: %s' % str(e))
        notify_slack_error(str(e), 'post_core_data_json')
        return str(e), 400

    # we construct the batch from the push context
    context = payload['context']
    flask.current_app.logger.info('Creating new batch from context: %s' % context)
    batch = Batch(**context)
    batch.user = get_jwt_identity()
    db.session.add(batch)
    db.session.flush()  # this sets the batch ID, which we need for corresponding coreData objects

    # add states
    state_dicts = payload['states']
    state_objects = []
    for state_dict in state_dicts:
        state_pk = state_dict['state']
        state_obj = db.session.query(State).get(state_pk)
        if state_obj is not None:
            flask.current_app.logger.info('Updating state row from info: %s' % state_dict)
            db.session.query(State).filter_by(state=state_pk).update(state_dict)
            # this method of updating does not trigger validators, so validate manually
            state_obj.validate_totalTestResultsFieldDbColumn(None, state_obj.totalTestResultsFieldDbColumn)
            state_objects.append(state_obj)  # return updated state
        else:
            flask.current_app.logger.info('Creating new state row from info: %s' % state_dict)
            state = State(**state_dict)
            db.session.add(state)
            state_objects.append(state)

        db.session.flush()

    # add all core data rows
    core_data_dicts = payload['coreData']
    core_data_objects = []
    for core_data_dict in core_data_dicts:
        flask.current_app.logger.info('Creating new core data row: %s' % core_data_dict)
        core_data_dict['batchId'] = batch.batchId
        core_data = CoreData(**core_data_dict)
        db.session.add(core_data)
        core_data_objects.append(core_data)

    db.session.flush()

    # construct the JSON before committing the session, since sqlalchemy objects behave weirdly
    # once the session has been committed
    json_to_return = {
        'batch': batch.to_dict(),
        'coreData': [core_data.to_dict() for core_data in core_data_objects],
        'states': [state.to_dict() for state in state_objects],
    }

    db.session.commit()

    # this returns a tuple of flask response and status code: (flask.Response, int)
    return flask.jsonify(json_to_return), 201


@api.route('/batches', methods=['POST'])
@jwt_required
@exceptions_to_slack
def post_core_data():
    """
    Workhorse POST method for core data

    Requirements:
    """
    flask.current_app.logger.info('Received a CoreData write request')
    payload = flask.request.json  # this is a dict

    post_result = post_core_data_json(payload)
    status_code = post_result[1]
    if status_code == 201:
        batch_info = post_result[0].json['batch']
        notify_slack(f"*Pushed batch #{batch_info['batchId']}* (type: {batch_info['dataEntryType']}, user: {batch_info['shiftLead']})\n"
                     f"{batch_info['batchNote']}")

    return post_result


def any_existing_rows(state, date):
    date = CoreData.parse_str_to_date(date)
    existing_rows = db.session.query(CoreData).join(Batch).filter(
        Batch.isPublished == True,
        CoreData.state == state,
        CoreData.date == date).all()
    return len(existing_rows) > 0


@api.route('/batches/edit', methods=['POST'])
@jwt_required
@notify_webhook
@exceptions_to_slack
def edit_core_data():
    flask.current_app.logger.info('Received a CoreData edit request')
    payload = flask.request.json

    # test input data
    try:
        validate_edit_data_payload(payload)
    except ValueError as e:
        flask.current_app.logger.error("Edit data failed validation: %s" % str(e))
        notify_slack_error(str(e), 'edit_core_data')
        return str(e), 400

    context = payload['context']
    core_data = payload['coreData']
    return edit_states_daily_internal(get_jwt_identity(), context, core_data)


@api.route('/batches/edit_states_daily', methods=['POST'])
@jwt_required
@notify_webhook
@exceptions_to_slack
def edit_core_data_from_states_daily():
    payload = flask.request.json
    flask.current_app.logger.info('Received a CoreData States Daily edit request: %s' % payload)

    # test input data
    try:
        validate_edit_data_payload(payload)
    except ValueError as e:
        flask.current_app.logger.error("Edit data failed validation: %s" % str(e))
        notify_slack_error(str(e), 'edit_core_data_from_states_daily')
        return str(e), 400

    # we construct the batch from the push context
    context = payload['context']

    # check that the state is set
    state_to_edit = context.get('state')
    if not state_to_edit:
        flask.current_app.logger.error("No state specified in batch edit context: %s" % str(context))
        notify_slack_error(
            'No state specified in batch edit context', 'edit_core_data_from_states_daily')
        return 'No state specified in batch edit context', 400

    core_data = payload['coreData']
    return edit_states_daily_internal(
        get_jwt_identity(), context, core_data, state_to_edit, publish=True)

def edit_states_daily_internal(user, context, core_data, state_to_edit=None, publish=False):
    flask.current_app.logger.info('Creating new batch from context: %s' % context)

    batch = Batch(**context)
    batch.user = user
    batch.isRevision = True
    batch.isPublished = publish
    if publish:
        batch.publishedAt = datetime.utcnow()
    db.session.add(batch)
    db.session.flush()  # this sets the batch ID, which we need for corresponding coreData objects

    latest_daily_data_for_state = states_daily_query(state=state_to_edit).all()

    # split up by date for easier lookup/comparison with input edit rows
    date_to_data = {}
    for state_daily_data in latest_daily_data_for_state:
        date_to_data[state_daily_data.date] = state_daily_data

    # keep track of all our changes as we go
    core_data_objects = []
    changed_rows = []
    new_rows = []

    # check each core data row that the corresponding date/state already exists in published form
    for core_data_dict in core_data:
        # this state has to be identical to the state from the context
        state = core_data_dict['state']
        if state_to_edit and state != state_to_edit:
            error = 'Context state %s does not match JSON data state %s' % (state_to_edit, state)
            flask.current_app.logger.error(error)
            notify_slack_error(error, 'edit_core_data_from_states_daily')
            return error, 400

        valid, unknown = CoreData.valid_fields_checker(core_data_dict)
        if not valid:
            # there are no fields to add/update
            flask.current_app.logger.info('Got row without updates, skipping. %r' % core_data_dict)
            continue

        if unknown:
            # report unknown fields, we won't fail the request, but should at least log
            flask.current_app.logger.warning('Got row with unknown field updates. %r' % core_data_dict)

        # is there a date for this?
        # check that there exists at least one published row for this date/state
        date = CoreData.parse_str_to_date(core_data_dict['date'])
        data_for_date = date_to_data.get(date)
        core_data_dict['batchId'] = batch.batchId
        edited_core_data = None

        if not data_for_date:
            # this is a new row: we treat this as a changed date

            # TODO: uncomment these 3 lines if we want to enforce editing only existing date rows
            # error = 'Attempting to edit a nonexistent date: %s' % core_data_dict['date']
            # flask.current_app.logger.error(error)
            # return flask.jsonify(error), 400

            flask.current_app.logger.info('Row for date not found, making new edit row: %s' % date)
            edited_core_data = CoreData(**core_data_dict)
            new_rows.append(edited_core_data)
        else:
            # this row already exists, but check each value to see if anything changed. Easiest way
            changed_for_date = data_for_date.field_diffs(core_data_dict)
            if changed_for_date:
                changed_rows.append(changed_for_date)
                edited_core_data = data_for_date.copy_with_updates(**core_data_dict)

        # if any value in the row is different, make an edit batch
        if edited_core_data:
            # store the changes
            db.session.add(edited_core_data)
            core_data_objects.append(edited_core_data)
            db.session.flush()
            flask.current_app.logger.info('Adding new edit row: %s' % edited_core_data.to_dict())
        else:
            # there were no changes
            flask.current_app.logger.info('All values are the same for date %s, ignoring' % date)

    db.session.flush()

    diffs = EditDiff(changed_rows, new_rows)
    if diffs.is_empty():
        # there are no changes, nothing to do
        notify_slack_error(
            f"*Received edit batch #{batch.batchId}*. state: {state_to_edit}. (user: {batch.shiftLead})\n"
            f"{batch.batchNote} but no differences detected, data is unchanged", "edit_states_daily")

        return 'Data is unchanged: no edits detected', 400

    batch.changedFields = diffs.changed_fields
    batch.numRowsEdited = diffs.size()
    db.session.flush()

    # TODO: change consumer of this response to use the changedFields, changedDates, numRowsEdited
    # from the "batch" object, then remove those keys from the JSON response
    json_to_return = {
        'batch': batch.to_dict(),
        'changedFields': batch.changedFields,
        'changedDates': diffs.changed_dates_str,
        'numRowsEdited': batch.numRowsEdited,
        'user': get_jwt_identity(),
        'coreData': [core_data.to_dict() for core_data in core_data_objects],
    }

    db.session.commit()

    # collect all the diffs for the edits we've made and format them for a slack notification
    diffs_for_slack = diffs.plain_text_format()

    notify_slack(
        f"*Pushed and published edit batch #{batch.batchId}*. state: {state_to_edit}. (user: {batch.shiftLead})\n"
        f"{batch.batchNote}", diffs_for_slack)

    return flask.jsonify(json_to_return), 201


# Get all published rows for this state and date, in reverse chronological order
@api.route('/state-date-history/<string:state>/<string:date>', methods=['GET'])
def get_state_date_history(state, date):
    flask.current_app.logger.info('Retrieving state date history')

    history = db.session.query(CoreData).join(Batch).filter(
        Batch.isPublished == True,
        CoreData.state == state.upper(),
        CoreData.date == date
        ).order_by(CoreData.batchId.desc()).all()

    return_history = []
    for elem in history:
        return_elem = elem.to_dict()
        return_elem['batch'] = elem.batch.to_dict()
        del return_elem['batch']['coreData']
        return_history.append(return_elem)

    return flask.jsonify(return_history)
