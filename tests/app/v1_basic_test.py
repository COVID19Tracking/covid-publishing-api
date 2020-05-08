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

def test_batch_models(app):
    # `db` is only valid within an app context, so start one and then shove some test data into it.
    with app.app_context():
        bat = Batch(batch_note='test', created_at=datetime.now(),
            is_published=False, is_revision=False)
        db.session.add(bat)
        db.session.commit()

    client = app.test_client()
    resp_json = client.get("/api/v1/data/batch/").json
    assert "batches" in resp_json
    assert resp_json['batches'][0]['batch_note'] == 'test'

def test_states(app):
    with app.app_context():
        nys = State(state_name='NY', full_name="New York")
        db.session.add(nys)
        db.session.commit()
    
    client = app.test_client()
    resp_json = client.get("/api/v1/data/state/").json
    assert "states" in resp_json
    assert resp_json['states'][0]['full_name'] == 'New York'
    assert resp_json['states'][0]['state_name'] == 'NY'

def test_core_data(app):
    with app.app_context():
        nys = State(state_name='NY')
        bat = Batch(batch_note='test', created_at=datetime.now(),
            is_published=False, is_revision=False)
        db.session.add(bat)
        db.session.flush()

        assert bat.batch_id == 1
        core_data_row = CoreData(
            last_update_time = datetime.now(), last_check_time = datetime.now(),
            data_date = datetime.today(), state_name='NY', batch_id=bat.batch_id)
        
        db.session.add(nys)
        db.session.add(core_data_row)

        db.session.commit()

    client = app.test_client()
    resp_json = client.get("/api/v1/data/").json
    assert len(resp_json['data']) == 1
    core_data_returned_row = resp_json['data'][0]

    # make sure the batch object also represented here, as a parent row
    assert 'batch' in core_data_returned_row
    assert core_data_returned_row['batch_id'] == core_data_returned_row['batch']['batch_id']
    
