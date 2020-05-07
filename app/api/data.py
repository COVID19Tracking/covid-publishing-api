"""Registers the necessary routes for the core data model. """

from flask import jsonify, request, current_app, abort
from app.api import api
from app.models.data import *
from app import db


@api.route('/test/', methods=['GET'])
def get_data():
    current_app.logger.info('Retrieving all data: placeholder')
    current_app.logger.debug('This is a debug log')
    return jsonify({'test_data_key': 'test_data_value'})


@api.route('/data/batch/', methods=['GET'])
def get_batches():
    current_app.logger.info('Retrieving all batches')
    batches = Batch.query.all()
    return jsonify({
        'batches': [batch.to_dict() for batch in batches]
    })

@api.route('/data/state/', methods=['GET'])
def get_states():
    current_app.logger.info('Retrieving all states')
    states = States.query.all()
    return jsonify({
        'states': [state.to_dict() for state in states]
    })

@api.route('/data/', methods=['GET'])
def get_core_data():
    current_app.logger.info('Retrieving all states')
    data = CoreData.query.join(Batch).join(State).all()
    # import pdb; pdb.set_trace()
    return jsonify({
        'data': [x.to_dict() for x in data]
    }) 

@api.route('/data/batch/', methods=['POST'])
def post_data():
    current_app.logger.info('Got a post request!')
    payload = request.json
    if not payload:
        abort(400)
    current_app.logger.info(payload)
    return jsonify({'payload': payload})
