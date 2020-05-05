"""Registers the necessary routes for the core data model. """

from flask import jsonify, request, current_app
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

@api.route('/data/batch/', methods=['POST'])
def post_data():
    current_app.logger.info('Got a post request!')
    payload = request.json
    current_app.logger.info(payload)
    return jsonify({'payload': payload})
