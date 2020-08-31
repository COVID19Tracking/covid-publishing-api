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

from common import daily_push_ny_wa_two_days


def test_get_state_info(app):
    client = app.test_client()
    with app.app_context():
        nys = State(state='NY', name='New York', pum=False, notes='Testing123')
        wa = State(state='WA', name='Washington', pum=False, notes='Testing321')
        db.session.add(nys)
        db.session.add(wa)
        db.session.commit()

    resp = client.get("/api/v1/public/states/info")
    assert resp.status_code == 200
    respjson = resp.json
    assert len(respjson) == 2
    assert respjson[0]["pum"] == False
    assert respjson[0]["notes"] == 'Testing123'

    resp = client.get("/api/v1/public/states/info.csv")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").splitlines()
    reader = csv.DictReader(lines, delimiter=',')
    cnt = 0
    for row in reader:
        cnt += 1
        assert row["State"] in ["NY", "WA"]
        assert row["Notes"] in ["Testing123", "Testing321"]
    assert cnt == 2


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
    assert len(resp.json) == 56

    # publish it, make sure the data comes back
    resp = client.post('/api/v1/batches/1/publish')
    assert resp.status_code == 401 # should fail without authentication
    resp = client.post('/api/v1/batches/1/publish', headers=headers)
    assert resp.status_code == 201

    resp = client.get("/api/v1/public/states/daily")
    assert resp.status_code == 200
    # check that we returned all states
    assert len(resp.json) == 56
    assert resp.json == unpublished_version

    # check that the states are sorted alphabetically - test data should be just one date
    returned_states = [x['state'] for x in resp.json]
    assert returned_states == sorted(returned_states)

    # check that the "preview" request now returns nothing, since we've published the batch
    resp = client.get("/api/v1/public/states/daily?preview=true")
    assert resp.status_code == 200
    assert resp.json == []

    resp = client.get("/api/v1/public/states/daily.csv")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").splitlines()
    assert len(lines) == 57
    reader = csv.DictReader(lines, delimiter=',')
    data = list(reader)
    assert data[0]["Date"] == '20200618'
    assert data[0]["Positive"] == "708"
    assert data[0]["Negative"] == "80477"


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

    assert resp.json[1]['date'] == '2020-05-24'
    assert resp.json[1]['positive'] == 24
    assert resp.json[1]['negative'] == 12


def test_get_us_states_csv(app, headers):
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

    # Publish the new batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id),
                       headers=headers)
    assert resp.status_code == 201

    # test US daily CSV
    resp = client.get("/api/v1/public/us/daily.csv")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").splitlines()
    assert len(lines) == 3
    reader = csv.DictReader(lines, delimiter=',')
    data = list(reader)

    assert data[0]["Date"] == '20200525'
    assert data[0]["States"] == "2"
    assert data[0]["Positive"] == "30"
    assert data[0]["Negative"] == "15"

    assert data[1]["Date"] == '20200524'
    assert data[1]["States"] == "2"
    assert data[1]["Positive"] == "24"
    assert data[1]["Negative"] == "12"

    # test states current CSV
    resp = client.get("/api/v1/public/states/current.csv")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").splitlines()
    assert len(lines) == 3
    reader = csv.DictReader(lines, delimiter=',')
    data = list(reader)

    # test states current CSV
    resp = client.get("/api/v1/public/states/current.csv")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").splitlines()
    assert len(lines) == 3
    reader = csv.DictReader(lines, delimiter=',')
    data = list(reader)

    assert len(data) == 2
    assert "Date" not in data[0]
    assert data[0]["State"] == "NY"
    assert data[0]["Positive"] == "20"
    assert data[0]["Negative"] == "5"
    assert data[1]["State"] == "WA"
    assert data[1]["Positive"] == "10"
    assert data[1]["Negative"] == "10"

    # test US current CSV
    resp = client.get("/api/v1/public/us/current.csv")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").splitlines()
    assert len(lines) == 2
    reader = csv.DictReader(lines, delimiter=',')
    data = list(reader)

    # US current shouldn't have date and state columns
    assert "Date" not in data[0]
    assert "State" not in data[0]
    assert "Deaths" in data[0]
    assert data[0]["Positive"] == "30"
    assert data[0]["Negative"] == "15"


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
