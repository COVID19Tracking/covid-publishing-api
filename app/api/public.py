"""Registers the necessary routes for the public API endpoints."""

from flask import jsonify, request, current_app, abort
from app.api import api
from app.models.data import *
from app import db

##############################################################################################
######################################   States      #########################################
##############################################################################################

@api.route('/public/states/info', methods=['GET'])
def get_states():
    states = State.query.all()
    return jsonify(
        [state.to_dict() for state in states]
    )
