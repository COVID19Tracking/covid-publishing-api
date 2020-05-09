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
        bat = Batch(batchNote='test', createdAt=datetime.now(),
            isPublished=False, isRevision=False)
        db.session.add(bat)
        db.session.commit()

    client = app.test_client()
    resp_json = client.get("/api/v1/data/batch/").json
    assert "batches" in resp_json
    assert resp_json['batches'][0]['batchNote'] == 'test'


def test_states(app):
    with app.app_context():
        nys = State(state='NY', fullName="New York")
        db.session.add(nys)
        db.session.commit()
    
    client = app.test_client()
    resp_json = client.get("/api/v1/data/state/").json
    assert "states" in resp_json
    assert resp_json['states'][0]['fullName'] == 'New York'
    assert resp_json['states'][0]['state'] == 'NY'


def _add_test_data(context_db):
    nys = State(state='NY')
    bat = Batch(batchNote='test', createdAt=datetime.now(),
        isPublished=False, isRevision=False)
    context_db.session.add(bat)
    context_db.session.add(nys)
    context_db.session.flush()

    core_data_row = CoreData(
        lastUpdateTime = datetime.now(), lastCheckTime = datetime.now(),
        date = datetime.today(), state='NY', batchId=bat.batchId)
    
    context_db.session.add(core_data_row)
    context_db.session.commit()


def test_core_data_model(app):
    with app.app_context():
        _add_test_data(db)

        states = State.query.all()
        assert len(states) == 1
        state = states[0]
        assert state.state == 'NY'
        assert state.to_dict() == {'state': 'NY'}

        batches = Batch.query.all()
        assert len(batches) == 1
        batch = batches[0]
        assert batch.batchId == 1

        core_data_all = CoreData.query.all()
        assert len(core_data_all) == 1
        core_data_row = core_data_all[0]
        assert core_data_row.batchId == batch.batchId
        assert core_data_row.state == state.state
        
        # check that the Batch object is attached to this CoreData object
        assert core_data_row.batch == batch
        # also check the relationship in the other direction, that CoreData is attached to the batch
        assert len(batch.coreData) == 1
        assert batch.coreData[0] == core_data_row


def test_core_data_get(app):
    with app.app_context():
        _add_test_data(db)

    client = app.test_client()
    resp_json = client.get("/api/v1/data/").json
    assert len(resp_json['data']) == 1
    core_data_returned_row = resp_json['data'][0]

    # make sure the batch object also represented here, as a parent row
    assert 'batch' in core_data_returned_row
    assert core_data_returned_row['batchId'] == core_data_returned_row['batch']['batchId']
