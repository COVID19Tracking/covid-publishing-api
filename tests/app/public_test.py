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

from common import daily_push_ny_wa_two_days, daily_push_ny_ca_total_test_results_different_source


def test_get_state_info(app):
    client = app.test_client()
    with app.app_context():
        nys = State(state='NY', name='New York', pum=False, notes='Testing123',
            totalTestResultsFieldDbColumn="totalTestsViral")
        wa = State(state='WA', name='Washington', pum=False, notes='Testing321',
            totalTestResultsFieldDbColumn="totalTestsViral")
        db.session.add(nys)
        db.session.add(wa)
        db.session.commit()

    resp = client.get("/api/v1/public/states/info")
    assert resp.status_code == 200
    respjson = resp.json
    assert len(respjson) == 2
    assert respjson[0]["pum"] == False
    assert respjson[0]["notes"] == 'Testing123'
    assert respjson[0]["totalTestResultsFieldDbColumn"] == 'totalTestsViral'


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

    # should still be no data if we explicitly set preview=false
    resp = client.get("/api/v1/public/states/daily?preview=false")
    assert resp.status_code == 200
    assert resp.json == []

    # set the preview flag to get unpublished data
    resp = client.get("/api/v1/public/states/daily?preview=true")
    assert resp.status_code == 200
    # batch hasn't been published
    unpublished_version = resp.json
    assert len(resp.json) == 56 * 2

    # publish it, make sure the data comes back
    resp = client.post('/api/v1/batches/1/publish')
    assert resp.status_code == 401 # should fail without authentication
    resp = client.post('/api/v1/batches/1/publish', headers=headers)
    assert resp.status_code == 201

    resp = client.get("/api/v1/public/states/daily")
    assert resp.status_code == 200
    # check that we returned all states
    assert len(resp.json) == 56 * 2
    assert resp.json == unpublished_version

    # check that the states are sorted alphabetically, doubled - test data is 2 days
    returned_states = [x['state'] for x in resp.json]
    set1 = sorted(list(set(returned_states)))
    assert returned_states == set1 + set1

    # check that there are 2 different dates
    returned_dates = list(set([x['date'] for x in resp.json]))
    assert len(returned_dates) == 2

    # check that the "preview" request now returns nothing, since we've published the batch
    resp = client.get("/api/v1/public/states/daily?preview=true")
    assert resp.status_code == 200
    assert resp.json == []


def test_get_us_daily_column_names(app):
    colnames = CoreData.numeric_fields()
    assert 'positive' in colnames
    assert 'checker' not in colnames


def test_get_us_daily(app, headers):
    test_data = daily_push_ny_wa_two_days()
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

    # but it should appear if we ask for preview data
    resp = client.get("/api/v1/public/us/daily?preview=true")
    assert resp.status_code == 200
    assert len(resp.json) == 2

    # Publish the new batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id),
                       headers=headers)
    assert resp.status_code == 201

    resp = client.get("/api/v1/public/us/daily")
    assert resp.status_code == 200
    assert len(resp.json) == 2

    # should come back in reverse chronological order
    assert resp.json[0]['date'] == '2020-05-25'
    assert resp.json[0]['positive'] == 30
    assert resp.json[0]['negative'] == 15
    # check that totalTestResult aggregation works as expected
    assert resp.json[0]['totalTestResults'] == 45

    assert resp.json[1]['date'] == '2020-05-24'
    assert resp.json[1]['positive'] == 24
    assert resp.json[1]['negative'] == 12
    assert resp.json[1]['totalTestResults'] == 36


def test_get_us_daily_some_null_totals(app, headers):
    test_data = daily_push_ny_ca_total_test_results_different_source()
    client = app.test_client()

    # Write a batch containing the above data, two days each of NY and WA and one day for CA. But,
    # CA has a different totalTestResults source, and so should not be counted in the totals data.
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(test_data),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']
    # Publish the batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id),
                       headers=headers)
    assert resp.status_code == 201

    resp = client.get("/api/v1/public/us/daily")
    assert resp.status_code == 200
    assert len(resp.json) == 2

    # should come back in reverse chronological order and include CA's positives or negatives
    assert resp.json[0]['date'] == '2020-05-25'
    assert resp.json[0]['positive'] == 40
    assert resp.json[0]['negative'] == 20
    # but totalTestResult aggregation should NOT include CA
    assert resp.json[0]['totalTestResults'] == 45

    assert resp.json[1]['date'] == '2020-05-24'
    assert resp.json[1]['positive'] == 24
    assert resp.json[1]['negative'] == 12
    assert resp.json[1]['totalTestResults'] == 36


def test_get_states_daily_for_state(app, headers):
    test_data = daily_push_ny_wa_two_days()
    client = app.test_client()

    # Write a batch containing the above data, two days each of NY and WA
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(test_data),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']

    resp = client.get("/api/v1/public/states/ny/daily?preview=true")
    assert len(resp.json) == 2

    # publish batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id), headers=headers)

    # shouldn't work for "ZZ", but should work for both "ny" and "NY"
    resp = client.get("/api/v1/public/states/ZZ/daily")
    assert resp.status_code == 404

    resp = client.get("/api/v1/public/states/ny/daily")
    assert len(resp.json) == 2
    resp = client.get("/api/v1/public/states/NY/daily")
    assert len(resp.json) == 2

    # should come back in reverse chronological order
    assert resp.json[0]['date'] == '2020-05-25'
    assert resp.json[0]['positive'] == 20
    assert resp.json[0]['negative'] == 5

    assert resp.json[1]['date'] == '2020-05-24'
    assert resp.json[1]['positive'] == 15
    assert resp.json[1]['negative'] == 4
