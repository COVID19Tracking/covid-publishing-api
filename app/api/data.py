"""Registers the necessary routes for the core data model. """
import flask

from app.api import api
from app.models.data import *
from app.utils.webhook import notify_webhook
from app import db
from flask_jwt_extended import jwt_required

from datetime import datetime

from sqlalchemy import func, and_

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
    return flask.jsonify({'user': 'authenticated'}),200

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

    notify_webhook()

    return flask.jsonify(batch.to_dict()), 201


##############################################################################################
######################################   Core data      ######################################
##############################################################################################


# Expects a dictionary of push context, state info, and core data rows. Writes to DB.
def post_core_data_json(payload):
    # test the input data
    if 'context' not in payload:
        return flask.Response("Payload requires 'context' field", status=400)
    if 'states' not in payload:
        return flask.Response("Payload requires 'states' field", status=400)
    if 'coreData' not in payload:
        return flask.Response("Payload requires 'coreData' field", status=400)

    # we construct the batch from the push context
    context = payload['context']
    flask.current_app.logger.info('Creating new batch from context: %s' % context)
    batch = Batch(**context)
    db.session.add(batch)
    db.session.flush()  # this sets the batch ID, which we need for corresponding coreData objects

    # add states
    state_dicts = payload['states']
    state_objects = []
    for state_dict in state_dicts: 
        state_pk = state_dict['state']
        if db.session.query(State).get(state_pk) is not None:
            flask.current_app.logger.info('Updating state row from info: %s' % state_dict)
            db.session.query(State).filter_by(state=state_pk).update(state_dict)
            state_objects.append(db.session.query(State).get(state_pk))  # return updated state
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
    return flask.jsonify(json_to_return), 201


@api.route('/batches', methods=['POST'])
@jwt_required
def post_core_data():
    """
    Workhorse POST method for core data

    Requirements: 
    """
    flask.current_app.logger.info('Received a CoreData write request')
    payload = flask.request.json  # this is a dict

    return post_core_data_json(payload)

def edit_core_data():
    flask.current_app.logger.info('Received a CoreData edit request')
