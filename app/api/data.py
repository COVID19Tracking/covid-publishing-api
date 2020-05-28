"""Registers the necessary routes for the core data model. """

from flask import jsonify, request, current_app, abort
from app.api import api
from app.models.data import *
from app import db

from datetime import datetime

from sqlalchemy import func, and_

##############################################################################################
######################################   Health check      ###################################
##############################################################################################


@api.route('/test', methods=['GET'])
def get_data():
    current_app.logger.info('Retrieving all data: placeholder')
    current_app.logger.debug('This is a debug log')
    return jsonify({'test_data_key': 'test_data_value'})


##############################################################################################
######################################   Batches      ########################################
##############################################################################################


@api.route('/batches', methods=['GET'])
def get_batches():
    current_app.logger.info('Retrieving all batches')
    batches = Batch.query.all()
    # for each batch, attach its coreData rows
    
    return jsonify({
        'batches': [batch.to_dict() for batch in batches]
    })


@api.route('/batches/<int:id>', methods=['GET'])
def get_batch_by_id(id):
    batch = Batch.query.get_or_404(id)
    current_app.logger.info('Returning batch %d' % id)
    return jsonify(batch.to_dict())


@api.route('/batches/<int:id>/publish', methods=['POST'])
def publish_batch(id):
    current_app.logger.info('Received request to publish batch %d' % id)
    batch = Batch.query.get_or_404(id)

    # if batch is already published, fail out
    if batch.isPublished:
        return 'Batch %d already published, rejecting double-publish' % id, 422

    batch.isPublished = True
    batch.publishedAt = datetime.utcnow()   # set publish time to now
    db.session.add(batch)
    db.session.commit()
    return jsonify(batch.to_dict()), 201


##############################################################################################
######################################   Core data      ######################################
##############################################################################################


@api.route('/batches', methods=['POST'])
def post_core_data():
    """
    Workhorse POST method for core data

    Requirements: 
    """
    current_app.logger.info('Got a post request!')
    payload = request.json  # this is a dict

    # test the input data
    # TODO: return a status 400 (or maybe 422) with an array of validation errors when assertions
    # like these fail.
    assert 'context' in payload, "Payload requires 'context' field"
    assert 'states' in payload, "Payload requires 'states' field"
    assert 'coreData' in payload, "Payload requires 'coreData' field"

    # we construct the batch from the push context
    context = payload['context']
    current_app.logger.info('Creating new batch from context: %s' % context)
    batch = Batch(**context)
    db.session.add(batch)
    db.session.flush()  # this sets the batch ID, which we need for corresponding coreData objects

    # add states
    state_dicts = payload['states']
    state_objects = []
    for state_dict in state_dicts: 
        state_pk = state_dict['state']
        if db.session.query(State).get(state_pk) is not None:
            current_app.logger.info('Updating state row from info: %s' % state_dict)
            db.session.query(State).filter_by(state=state_pk).update(state_dict)
            state_objects.append(db.session.query(State).get(state_pk))  # return updated state
        else:
            current_app.logger.info('Creating new state row from info: %s' % state_dict)
            state = State(**state_dict)
            db.session.add(state)
            state_objects.append(state)

        db.session.flush()

    # add all core data rows
    core_data_dicts = payload['coreData']
    core_data_objects = []
    for core_data_dict in core_data_dicts:
        current_app.logger.info('Creating new core data row: %s' % core_data_dict)
        core_data_dict['batchId'] = batch.batchId
        core_data = CoreData(**core_data_dict)
        db.session.add(core_data)
        core_data_objects.append(core_data)

    db.session.commit()
    return jsonify({
        'batch': batch.to_dict(),
        'coreData': [core_data.to_dict() for core_data in core_data_objects],
        'states': [state.to_dict() for state in state_objects]
    }), 201
