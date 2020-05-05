"""
Basic Test for V1 of API
"""
import pytest
from rest_tester import RestTester

@pytest.fixture
def endpoint() -> RestTester:
    return RestTester("http://localhost:5000/api/v1")

def test_get_test(endpoint):
    x = endpoint.get("/test")
    assert(x != None)
    assert("test_data_key" in x)
    assert(x["test_data_key"] == "test_data_value")
