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
        nys = State(state='NY', name='New York', pum=False, notes='Testing123')
        wa = State(state='WA', name='Washington', pum=False, notes='Testing123')
        db.session.add(nys)
        db.session.add(wa)
        db.session.commit()

    resp = client.get("/api/v1/public/states/info")
    assert resp.status_code == 200
    respjson = resp.json
    assert len(respjson) == 2
    assert respjson[0]["pum"] == False
    assert respjson[0]["notes"] == 'Testing123'