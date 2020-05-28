"""
Basic Test for V1 of API
"""
import os
import pytest

from flask import json, jsonify

from app import db
from app.models.data import *


def test_get_test(app):
    client = app.test_client()
    resp = client.get("/api/v1/test")
    assert resp.data != None 
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "test_data_key" in data 
    assert data["test_data_key"] == "test_data_value" 

def test_post_core_data(app, headers):
    client = app.test_client()

    example_filename = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(example_filename) as f:
        payload_json_str = f.read()

    # attempt to post data without an auth token
    resp = client.post(
        "/api/v1/batches",
        data=payload_json_str,
        content_type='application/json')
    assert resp.status_code == 401 # should fail with an authentication error

    resp = client.post(
        "/api/v1/batches",
        data=payload_json_str,
        content_type='application/json', 
        headers=headers)
    assert resp.status_code == 201

    # we should've written 56 states, 4 core data rows, 1 batch
    resp = client.get('/api/v1/public/states/info')
    assert len(resp.json) == 56
    assert resp.json[0]['state'] == "AK"
    assert resp.json[0]['twitter'] == "@Alaska_DHSS"

    resp = client.get('/api/v1/batches')
    assert len(resp.json['batches']) == 1
    assert resp.json['batches'][0]['batchId'] == 1
    # assert batch data has rows attached to it
    assert len(resp.json['batches'][0]['coreData']) == 56
    assert resp.json['batches'][0]['coreData'][1]['state'] == 'AL'
    assert resp.json['batches'][0]['coreData'][1]['antibodyTotal'] == 25

def test_post_core_data_updating_state(app, headers):
    with app.app_context():
        nys = State(state='AK', name='Alaska')
        db.session.add(nys)
        db.session.commit()

        states = State.query.all()
        assert len(states) == 1
        state = states[0]
        assert state.state == 'AK'
        assert state.to_dict() == {'state': 'AK', 'name': 'Alaska'}

    client = app.test_client()
    resp = client.get('/api/v1/public/states/info')
    assert resp.json[0]['state'] == "AK"
    # we haven't created this value yet
    assert 'twitter' not in resp.json[0]

    example_filename = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(example_filename) as f:
        payload_json_str = f.read()
    resp = client.post(
        "/api/v1/batches",
        data=payload_json_str,
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201

    # check that the last POST call updated the Alaska info, adding a "twitter" field from test file
    resp = client.get('/api/v1/public/states/info')
    assert resp.json[0]['state'] == "AK"
    assert resp.json[0]['twitter'] == "@Alaska_DHSS"

def test_get_batches(app):
    with app.app_context():
        # write 2 batches
        bat1 = Batch(batchNote='test1', createdAt=datetime.now(),
            isPublished=False, isRevision=False)
        bat2 = Batch(batchNote='test2', createdAt=datetime.now(),
            isPublished=False, isRevision=False)
        db.session.add(bat1)
        db.session.add(bat2)
        db.session.commit()

    client = app.test_client()
    resp = client.get('/api/v1/batches')
    assert resp.status_code == 200
    assert len(resp.json['batches']) == 2
    batch_notes = {x['batchNote'] for x in resp.json['batches']}
    assert batch_notes == {'test1', 'test2'}

    # get batch by ID
    resp = client.get('/api/v1/batches/1')
    assert resp.status_code == 200
    assert resp.json['batchId'] == 1
    assert resp.json['batchNote'] == 'test1'

def test_publish_batch(app):
    with app.app_context():
        # write 2 batches
        bat1 = Batch(batchNote='test1', createdAt=datetime.now(),
            isPublished=False, isRevision=False)
        bat2 = Batch(batchNote='test2', createdAt=datetime.now(),
            isPublished=False, isRevision=False)
        db.session.add(bat1)
        db.session.add(bat2)
        db.session.commit()

    client = app.test_client()
    resp = client.get('/api/v1/batches')
    assert resp.status_code == 200
    assert len(resp.json['batches']) == 2
    # check that both batches not published
    for batch in resp.json['batches']:
        assert batch['isPublished'] == False

    # publish the 2nd batch
    resp = client.post('/api/v1/batches/2/publish')
    assert resp.status_code == 201
    # this should've returned the published batch
    assert resp.json['batchId'] == 2
    assert resp.json['isPublished'] == True

    # check that the GET requests correctly reflect published status
    assert client.get('/api/v1/batches/1').json['isPublished'] == False
    assert client.get('/api/v1/batches/2').json['isPublished'] == True
