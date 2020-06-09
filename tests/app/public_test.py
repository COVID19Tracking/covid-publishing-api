"""
Tests for public API endpoints
"""
from datetime import date
from dateutil import parser
import os
import pytest

from flask import json, jsonify

from app import db
from app.models.data import *
from app.api.public import get_us_daily_column_names

def test_get_state_info(app):
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


def test_get_us_daily_column_names(app):
    colnames = get_us_daily_column_names()
    assert 'positive' in colnames
    assert 'checker' not in colnames
    assert len(colnames) == 22


# Test data used for testing US daily and states daily by state
def test_data_json_with_ny_wa_two_days():
    # TODO: Probably pull out some helpers to make this kind of
    # testing more succinct
    ny = {"state": "NY"}
    wa = {"state": "WA"}

    today = date(2020, 5, 25)
    yesterday = date(2020, 5, 24)

    ny_today = {
      "state": "NY",
      "lastUpdateIsoUtc": datetime.now().isoformat(),
      "dateChecked": datetime.now().isoformat(),
      "date": today,
      "positive": 20,
      "negative": 5
    }
    wa_today = {
      "state": "WA",
      "lastUpdateIsoUtc": datetime.now().isoformat(),
      "dateChecked": datetime.now().isoformat(),
      "date": today,
      "positive": 10,
      "negative": 10
    }
    ny_yest = {
      "state": "NY",
      "lastUpdateIsoUtc": datetime.now().isoformat(),
      "dateChecked": datetime.now().isoformat(),
      "date": yesterday,
      "positive": 15,
      "negative": 4
    }
    wa_yest = {
      "state": "WA",
      "lastUpdateIsoUtc": datetime.now().isoformat(),
      "dateChecked": datetime.now().isoformat(),
      "date": yesterday,
      "positive": 9,
      "negative": 8
    }

    ctx = {
      "dataEntryType": "daily",
      "shiftLead": "test",
      "batchNote": "This is a test"
    }
    test_data = {
      "context": ctx,
      "states": [ny, wa],
      "coreData": [ny_today, wa_today, ny_yest, wa_yest]
    }

    return test_data


def test_get_us_daily(app, headers):
    test_data = test_data_json_with_ny_wa_two_days()
    client = app.test_client()

    # Write a batch containing the above data, two days each of NY and WA
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(test_data),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']

    # We haven't published the batch yet, so we shouldn't have any data
    resp = client.get("/api/v1/public/us/daily")
    assert resp.status_code == 200
    assert len(resp.json) == 0

    # Publish the new batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id),
                       headers=headers)
    assert resp.status_code == 201

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


def test_get_states_daily_for_state(app, headers):
    test_data = test_data_json_with_ny_wa_two_days()
    client = app.test_client()

    # Write a batch containing the above data, two days each of NY and WA
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(test_data),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']
    # publish batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id), headers=headers)

    # shouldn't work for "ZZ", but should work for both "ny" and "NY"
    resp = client.get("/api/v1/public/states/daily/ZZ")
    assert resp.status_code == 404

    resp = client.get("/api/v1/public/states/daily/ny")
    assert len(resp.json) == 2
    resp = client.get("/api/v1/public/states/daily/NY")
    assert len(resp.json) == 2

    for day_data in resp.json:
        day = parser.parse(day_data['date']).day
        assert day in [24, 25]
        if day == 25:
            assert day_data['positive'] == 20
            assert day_data['negative'] == 5
        elif day == 24:
            assert day_data['positive'] == 15
            assert day_data['negative'] == 4
