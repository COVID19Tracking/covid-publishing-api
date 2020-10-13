"""
Tests for CSV generation code (CSV endpoints are tested in ``public_test.py``
"""
from app.api.csv import CSVColumn, make_csv_response

from flask import json, jsonify

from app import db
from app.models.data import *

from common import daily_push_ny_wa_two_days


def test_make_csv_response(app):
    columns = [CSVColumn(label="State", model_column="state"),
               CSVColumn(label="Twitter", model_column="twitter", blank=True),
               CSVColumn(label="Notes", model_column="note"),
               CSVColumn(label="Blank", model_column=None, blank=True)]

    assert columns[0].label == "State"
    assert columns[0].model_column == "state"
    assert columns[0].blank is False
    assert columns[1].blank is True

    data = [{"state": "CA", "note": "abc"},
            {"state": "NV", "note": "xyz", "twitter": "mystatetwitter"}]

    with app.app_context():
        resp = make_csv_response(columns, data)

        assert resp.headers["Content-type"] == "text/csv"
        data = resp.data.decode("utf-8").splitlines()
        assert data[0] == "State,Twitter,Notes,Blank"
        assert data[1] == "CA,,abc,"
        assert data[2] == "NV,,xyz,"


def test_get_state_info_csv(app):
    client = app.test_client()
    with app.app_context():
        nys = State(state='NY', name='New York', pum=False, notes='Testing123', totalTestResultsFieldDbColumn='posNeg')
        wa = State(state='WA', name='Washington', pum=False, notes='Testing321', totalTestResultsFieldDbColumn='posNeg')
        db.session.add(nys)
        db.session.add(wa)
        db.session.commit()

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


def test_get_states_daily_csv(app, headers):
    # post some test data
    client = app.test_client()

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

    resp = client.post('/api/v1/batches/1/publish', headers=headers)
    assert resp.status_code == 201

    resp = client.get("/api/v1/public/states/daily.csv")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").splitlines()
    assert len(lines) == 56 * 2 + 1
    reader = csv.DictReader(lines, delimiter=',')
    data = list(reader)
    assert data[0]["Date"] == '20200618'
    assert data[0]["Positive"] == "708"
    assert data[0]["Negative"] == "80477"

    assert data[56]["Date"] == '20200617'
    assert data[56]["Positive"] == "709"
    assert data[56]["Negative"] == "80477"


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

def test_get_latest_states_daily_csv(app, headers):
    # post some test data
    client = app.test_client()

    # prepare test data
    example_filename = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(example_filename) as f:
        payload_json_str = f.read()
    resp = client.post(
        "/api/v1/batches",
        data=payload_json_str,
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201

    resp = client.post('/api/v1/batches/1/publish', headers=headers)
    assert resp.status_code == 201

    resp = client.get("/api/v1/internal/states/daily.csv")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").splitlines()

    reader = csv.DictReader(lines, delimiter=',')
    data = list(reader)
    assert len(data) == 56
    assert data[0]["date"] == '20200618'
    assert data[0]["positive"] == "708"
    assert data[0]["negative"] == "80477"

    # 2 days
    resp = client.get("/api/v1/internal/states/daily.csv?days=2")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").splitlines()
    reader = csv.DictReader(lines, delimiter=',')
    data = list(reader)
    assert len(data) == 56 * 2
    assert data[0]["date"] == '20200618'
    assert data[0]["state"] == 'AK'
    assert data[0]["positive"] == "708"
    assert data[0]["totalTestsViral"] == "81185"

    assert data[56]["date"] == '20200617'
    assert data[56]["state"] == 'AK'
    assert data[56]["positive"] == "709"
    assert data[56]["totalTestsViral"] == "81185"

    # More days than we have
    resp = client.get("/api/v1/internal/states/daily.csv?days=5000")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").splitlines()
    reader = csv.DictReader(lines, delimiter=',')
    data = list(reader)
    assert len(data) == 56 * 2

    # US endpoints that use the same underlying method
    resp = client.get("/api/v1/public/us/current.csv")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").splitlines()
    reader = csv.DictReader(lines, delimiter=',')
    data = list(reader)
    assert len(data) == 1
    assert data[0]["Positive"] == "2177888"

    resp = client.get("/api/v1/public/us/daily.csv")
    assert resp.status_code == 200
    lines = resp.data.decode("utf-8").splitlines()
    reader = csv.DictReader(lines, delimiter=',')
    data = list(reader)
    assert len(data) == 2
    assert data[0]["Date"] == '20200618'
    assert data[0]["Positive"] == "2177888"
    assert data[1]["Date"] == '20200617'
    assert data[1]["Positive"] == "2177944"
