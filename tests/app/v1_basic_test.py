"""
Basic Test for V1 of API
"""
import pytest

from flask import json, jsonify

from app import db
from app.models.data import *

def test_get_test(app):
    client = app.test_client()
    resp = client.get("/api/v1/test/")
    assert resp.data != None 
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "test_data_key" in data 
    assert data["test_data_key"] == "test_data_value" 

def test_post(app):
    client = app.test_client()
    payload = {"testy": "mctest"}
    resp = client.post(
        "/api/v1/data/batch/",
        data=json.dumps(payload),
        content_type='application/json')
    data = json.loads(resp.data)
    assert data['payload'] == payload

    # check for error with empty payload
    payload = ''
    resp = client.post(
        "/api/v1/data/batch/",
        data=json.dumps(payload),
        content_type='application/json')
    assert resp.status_code == 400

def test_models(app):
    # `db` is only valid within an app context, so start one and then shove some test data into it.
    with app.app_context():
        bat = Batch(batch_note='test', created_at=datetime.now(), is_published=False, is_revision=False)
        db.session.add(bat)
        db.session.commit()

    client = app.test_client()
    resp = client.get("/api/v1/data/batch/")
    assert "batches" in resp.json
