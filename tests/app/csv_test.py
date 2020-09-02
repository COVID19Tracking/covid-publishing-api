"""
Tests for CSV generation code (CSV endpoints are tested in ``public_test.py``
"""
from app.api.csv import CSVColumn, make_csv_response


def test_csv(app):
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
