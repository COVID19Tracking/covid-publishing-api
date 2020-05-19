"""
Tests for public API endpoints
"""
import os
import pytest

from flask import json, jsonify

from app import db
from app.models.data import *

def test_get_states(app):
    client = app.test_client()
    with app.app_context():
        nys = State(state='NY', name='New York')
        wa = State(state='WA', name='Washington')
        db.session.add(nys)
        db.session.add(wa)
        db.session.commit()

    resp = client.get("/api/v1/public/states/info")
    assert resp.status_code == 200
    assert len(resp.json['states']) == 2