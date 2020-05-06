"""
Basic Test for V1 of API
"""
import psycopg2
import pytest
import sqlalchemy
import testing.postgresql

import app

from flask import json, jsonify

@pytest.fixture
def client():
    # Once we define a schema in this repo we can import it to start
    # with testing.postgresql.Postgresql(copy_data_from='ourschema.sql') as psql:
    with testing.postgresql.Postgresql() as psql:
        engine = sqlalchemy.create_engine(psql.url())
        yield app.create_app(engine).test_client()

def test_get_test(client):
    resp = client.get("/api/v1/test/")
    assert resp.data != None 
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "test_data_key" in data 
    assert data["test_data_key"] == "test_data_value" 

def test_post(client):
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
