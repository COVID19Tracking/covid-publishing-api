"""
Tests for public API endpoints
"""
from datetime import date
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

def test_get_states_daily(app, headers):
    # post some test data
    client = app.test_client()

    # TODO: for now, this is one day's worth of data. Need to expand this to multiple days, once
    # we start passing "date" in the JSON (right now inferring it). Then this test case will be more
    # meaningful
    example_filename = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(example_filename) as f:
        payload_json_str = f.read()
    resp = client.post(
        "/api/v1/batches",
        data=payload_json_str,
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201

    resp = client.get("/api/v1/public/states/daily")
    assert resp.status_code == 200
    # batch hasn't been published
    assert resp.json == []

    # publish it, make sure the data comes back
    resp = client.post('/api/v1/batches/1/publish')
    assert resp.status_code == 401 # should fail without authentication
    resp = client.post('/api/v1/batches/1/publish', headers=headers)
    assert resp.status_code == 201

    resp = client.get("/api/v1/public/states/daily")
    assert resp.status_code == 200
    # check that we returned all states
    assert len(resp.json) == 56

def test_get_us_daily(app, headers):
    with app.app_context():
        # add two states and a daily batch in publish mode
        db.session.add(State(state='NY'))
        db.session.add(State(state='WA'))
        bat = Batch(batchNote='test', createdAt=datetime.now(),
            isPublished=True, isRevision=False, dataEntryType='daily')
        db.session.add(bat)
        db.session.flush()

        today = date(2020, 5, 25)
        yesterday = date(2020, 5, 24)

        # add rows for today
        db.session.add(CoreData(
            lastUpdateIsoUtc=datetime.now().isoformat(), dateChecked=datetime.now().isoformat(),
            date=today, state='NY', batchId=bat.batchId,
            positive=20, negative=5))
        db.session.add(CoreData(
            lastUpdateIsoUtc=datetime.now().isoformat(), dateChecked=datetime.now().isoformat(),
            date=today, state='WA', batchId=bat.batchId,
            positive=10, negative=10))

        # add rows for yesterday
        db.session.add(CoreData(
            lastUpdateIsoUtc=datetime.now().isoformat(), dateChecked=datetime.now().isoformat(),
            date=yesterday, state='NY', batchId=bat.batchId,
            positive=15, negative=4))
        db.session.add(CoreData(
            lastUpdateIsoUtc=datetime.now().isoformat(), dateChecked=datetime.now().isoformat(),
            date=yesterday, state='WA', batchId=bat.batchId,
            positive=9, negative=8))

        db.session.commit()

        assert len(CoreData.query.all()) > 0
        assert len(Batch.query.all()) > 0

    client = app.test_client()
    resp = client.get("/api/v1/public/us/daily")
    assert resp.status_code == 200
    assert len(resp.json) == 2

    # expect 2 dates
    for day_data in resp.json:
        assert day_data['date'] in ['20200525', '20200524']
        if day_data['date'] == '20200525':
            assert day_data['positive'] == 30
            assert day_data['negative'] == 15
        elif day_data['date'] == '20200524':
            assert day_data['positive'] == 24
            assert day_data['negative'] == 12
