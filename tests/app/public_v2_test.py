"""
Tests for public API v2 endpoints
"""

from flask import json
import os
import pytest

from common import daily_push_ny_wa_two_days

from app.api.public_v2 import ValuesCalculator, CoreData, datetime, State, Batch, db, pytz


def write_and_publish_data(client, headers, data_json_str):
    # Write a batch containing two days each of NY and WA
    resp = client.post(
        "/api/v1/batches",
        data=data_json_str,
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id), headers=headers)
    assert resp.status_code == 201


def test_get_states_daily_basic(app, headers):
    client = app.test_client()

    # write and publish some test data
    example_filename = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(example_filename) as f:
        payload_json_str = f.read()
        write_and_publish_data(client, headers, payload_json_str)

    # can we read the data back out?
    resp = client.get("/api/v2/public/states/daily")
    assert resp.status_code == 200
    for k in ['links', 'meta', 'data']:
        assert k in resp.json

    # should have two days worth of data, for 56 states
    assert len(resp.json['data']) == 56 * 2

    # check that the states are sorted alphabetically, doubled - test data is 2 days
    returned_states = [x['state'] for x in resp.json['data']]
    set1 = sorted(list(set(returned_states)))
    assert returned_states == set1 + set1

    # check that there are 2 different dates
    returned_dates = list(set([x['date'] for x in resp.json['data']]))
    assert len(returned_dates) == 2

    # check that getting data for 1 state also works
    resp = client.get("/api/v2/public/states/NY/daily")
    assert resp.status_code == 200
    assert len(resp.json['data']) == 2
    returned_states = set([x['state'] for x in resp.json['data']])
    assert returned_states == {'NY'}


def test_get_states_daily_simple(app, headers):
    test_data = daily_push_ny_wa_two_days()   # two days each of NY and WA
    client = app.test_client()
    write_and_publish_data(client, headers, json.dumps(test_data))

    resp = client.get("/api/v2/public/states/daily/simple")
    assert resp.status_code == 200
    assert len(resp.json['data']) == 4  # should have 2 days of data for 2 states

    # should come back in reverse chronological order
    first_data = resp.json['data'][0]
    assert first_data['date'] == '2020-05-25'
    assert first_data['state'] == 'NY'
    assert first_data['tests']['pcr']['people']['positive'] == 20
    assert first_data['tests']['pcr']['people']['negative'] == 5

    second_data = resp.json['data'][1]
    assert second_data['date'] == '2020-05-25'
    assert second_data['state'] == 'WA'
    assert second_data['tests']['pcr']['people']['positive'] == 10
    assert second_data['tests']['pcr']['people']['negative'] == 10


def test_get_states_daily_full(app, headers):
    test_data = daily_push_ny_wa_two_days()   # two days each of NY and WA
    client = app.test_client()
    write_and_publish_data(client, headers, json.dumps(test_data))

    resp = client.get("/api/v2/public/states/daily")
    assert resp.status_code == 200
    assert len(resp.json['data']) == 4  # should have 2 days of data for 2 states

    # should come back in reverse chronological order
    first_data = resp.json['data'][0]
    assert first_data['date'] == '2020-05-25'
    assert first_data['state'] == 'NY'
    assert first_data['tests']['pcr']['people']['positive']['value'] == 20
    assert first_data['tests']['pcr']['people']['negative']['value'] == 5

    # make sure calculated values are correct
    assert first_data['tests']['pcr']['people']['positive']['calculated'] == {
        'population_percent': 0.0001,
        'change_from_prior_day': 5,
        'seven_day_average': 18,
        'seven_day_change_percent': None,
    }

    second_data = resp.json['data'][1]
    assert second_data['date'] == '2020-05-25'
    assert second_data['state'] == 'WA'
    assert second_data['tests']['pcr']['people']['positive']['value'] == 10
    assert second_data['tests']['pcr']['people']['negative']['value'] == 10


def test_values_calculator(app):
    with app.app_context():
        nys = State(state='NY', totalTestResultsFieldDbColumn='posNeg')
        bat = Batch(batchNote='test', createdAt=datetime.now(),
            isPublished=False, isRevision=False)
        db.session.add(bat)
        db.session.add(nys)
        db.session.flush()

        now_utc = datetime(2020, 5, 4, 20, 3, tzinfo=pytz.UTC)
        core_data_row = CoreData(
            lastUpdateIsoUtc=now_utc.isoformat(), dateChecked=now_utc.isoformat(),
            date=datetime.today(), state='NY', batchId=bat.batchId,
            positive=596214, negative=5, dataQualityGrade='A')

        calculator = ValuesCalculator([core_data_row])
        assert calculator.population_percent(core_data_row, 'positive') == 3.039
        assert calculator.calculate_values(core_data_row, 'dataQualityGrade') == None


def test_get_state_info_v2(app):
    client = app.test_client()
    with app.app_context():
        nys = State(state='NY', name='New York', pum=False, notes='Testing123',
            totalTestResultsFieldDbColumn="totalTestsViral", covid19Site="example.com")
        wa = State(state='WA', name='Washington', pum=False, notes='Testing321',
            totalTestResultsFieldDbColumn="totalTestsViral")
        db.session.add(nys)
        db.session.add(wa)
        db.session.commit()

    resp = client.get("/api/v2/public/states")
    assert resp.status_code == 200
    respjson = resp.json
    assert len(respjson['data']) == 2
    assert respjson['data'][0]['name'] == 'New York'
    assert respjson['data'][0]['census']['population'] == 19618453
    assert respjson['data'][0]['fips'] == '36'
    assert len(respjson['data'][0]['sites']) == 1  # undefined sites should be omitted
    assert respjson['data'][0]['sites'][0]['label'] == 'primary'


def test_get_us_daily(app, headers):
    test_data = daily_push_ny_wa_two_days()
    client = app.test_client()

    # Write and publish a batch containing the above data, two days each of NY and WA
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(test_data),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id),
                       headers=headers)
    assert resp.status_code == 201

    resp = client.get("/api/v2/public/us/daily")
    assert resp.status_code == 200
    assert len(resp.json['data']) == 2

    # should come back in reverse chronological order
    first_data = resp.json['data'][0]
    assert first_data['date'] == '2020-05-25'
    assert first_data['states'] == 2
    assert first_data['tests']['pcr']['people']['positive']['value'] == 30
    assert first_data['tests']['pcr']['people']['negative']['value'] == 15
    assert first_data['tests']['pcr']['total']['value'] == 45

    # make sure calculated values are correct
    assert first_data['tests']['pcr']['people']['positive']['calculated'] == {
        'population_percent': 0.0,
        'change_from_prior_day': 6,
        'seven_day_average': 27,
        'seven_day_change_percent': None,
    }

    second_data = resp.json['data'][1]
    assert second_data['date'] == '2020-05-24'
    assert second_data['states'] == 2
    assert second_data['tests']['pcr']['people']['positive']['value'] == 24
    assert second_data['tests']['pcr']['people']['negative']['value'] == 12
    assert second_data['tests']['pcr']['total']['value'] == 36
