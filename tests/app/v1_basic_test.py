"""
Basic Test for V1 of API
"""
import pytest

from flask import json, jsonify

def test_get_test(client):
    resp = client.get("/api/v1/test/")
    assert resp.data != None 
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "test_data_key" in data 
    assert data["test_data_key"] == "test_data_value" 


