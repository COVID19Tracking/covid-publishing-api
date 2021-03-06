"""
Basic Test for V1 of API
"""
from flask import json, jsonify

from app import db
from app.api.data import any_existing_rows
from app.models.data import *
from common import *
import datetime


def test_get_test(app):
    client = app.test_client()
    resp = client.get("/api/v1/test")
    assert resp.data != None
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert "test_data_key" in data
    assert data["test_data_key"] == "test_data_value"


def test_post_core_data(app, headers):
    client = app.test_client()

    example_filename = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(example_filename) as f:
        payload_json_str = f.read()

    # attempt to post data without an auth token
    resp = client.post(
        "/api/v1/batches",
        data=payload_json_str,
        content_type='application/json')
    assert resp.status_code == 401 # should fail with an authentication error

    resp = client.post(
        "/api/v1/batches",
        data=payload_json_str,
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201

    # we should've written 56 states times 2 days, 4 core data rows, 1 batch
    resp = client.get('/api/v1/public/states/info')
    assert len(resp.json) == 56
    assert resp.json[0]['state'] == "AK"
    assert resp.json[0]['twitter'] == "@Alaska_DHSS"

    resp = client.get('/api/v1/batches')
    assert len(resp.json['batches']) == 1
    assert resp.json['batches'][0]['batchId'] == 1
    assert resp.json['batches'][0]['user'] == 'testing'
    # assert batch data has rows attached to it
    assert len(resp.json['batches'][0]['coreData']) == 56 * 2

    # spot-check a few values
    assert resp.json['batches'][0]['coreData'][0]['state'] == 'AK'
    assert resp.json['batches'][0]['coreData'][0]['positive'] == 708
    # the entry for AK uses lastUpdateIsoUtc
    assert resp.json['batches'][0]['coreData'][0]['lastUpdateTime'] == '2020-06-18T04:00:00Z'

    assert resp.json['batches'][0]['coreData'][1]['state'] == 'AL'
    assert resp.json['batches'][0]['coreData'][1]['recovered'] == 15974
    # the entry for AL uses lastUpdateTime instead of lastUpdateIsoUtc, confirming it works
    assert resp.json['batches'][0]['coreData'][1]['lastUpdateTime'] == '2020-06-18T15:00:00Z'


def test_post_core_data_unknown_field(app, headers, slack_mock):
    client = app.test_client()

    # test an unknown field, simulating a bad/new column being sent to the DB
    bad_data = daily_push_ny_wa_today()
    bad_data["coreData"][0]["311"] = 42
    bad_data["coreData"][0]["lastUpdateIsoUtc"] = "2020-10-09T07:59:00Z"
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(bad_data),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 400
    resp_data = resp.data.decode("utf-8")
    assert resp_data == "Unknown field(s) in CoreData: 311"
    assert slack_mock.files_upload.call_count == 1


def test_post_core_data_updating_state(app, headers):
    with app.app_context():
        nys = State(state='AK', name='Alaska', totalTestResultsFieldDbColumn='totalTestsViral')
        db.session.add(nys)
        db.session.commit()

        states = State.query.all()
        assert len(states) == 1
        state = states[0]
        assert state.state == 'AK'
        assert state.to_dict() == {'state': 'AK', 'name': 'Alaska', 'pum': False, 'fips': '02',
                                   'population': 737068, 'totalTestResultsFieldDbColumn': 'totalTestsViral'}

    client = app.test_client()
    resp = client.get('/api/v1/public/states/info')
    assert resp.json[0]['state'] == "AK"
    # we haven't created this value yet
    assert 'twitter' not in resp.json[0]

    example_filename = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(example_filename) as f:
        payload_json_str = f.read()
    resp = client.post(
        "/api/v1/batches",
        data=payload_json_str,
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201

    # check that the last POST call updated the Alaska info, adding a "twitter" field from test file
    resp = client.get('/api/v1/public/states/info')
    assert resp.json[0]['state'] == "AK"
    assert resp.json[0]['twitter'] == "@Alaska_DHSS"
    # and setting totalTestResultsFieldDbColumn
    assert resp.json[0]['totalTestResultsFieldDbColumn'] == "totalTestEncountersViral"


def test_post_core_data_without_states(app, headers):
    client = app.test_client()
    example_filename = os.path.join(os.path.dirname(__file__), 'data.json')
    payload = json.load(open(example_filename))

    # insert initial data, with all states
    resp = client.post("/api/v1/batches",
                   data=json.dumps(payload),
                   content_type='application/json',
                   headers=headers)
    assert resp.status_code == 201

    # insert data without states, as non-research batch
    payload.pop('states')
    resp = client.post("/api/v1/batches",
                   data=json.dumps(payload),
                   content_type='application/json',
                   headers=headers)
    assert resp.status_code == 400


    # insert more data, without states
    coreData = payload.get('coreData')
    coreData = coreData[:2]
    for record in coreData:
        for k, v in record.items():
            if isinstance(v, int):
                record[k] = v + 1
            elif k == 'date':
                record[k] = datetime.datetime(2021, 3, 1)

    payload['coreData'] = coreData
    payload['context']['dataEntryType'] = 'research'
    resp = client.post("/api/v1/batches",
                   data=json.dumps(payload),
                   content_type='application/json',
                   headers=headers)
    assert resp.status_code == 201

    # we should've written 56 states times 3 days overall, some core data rows, 2 batch
    resp = client.get('/api/v1/batches')
    assert len(resp.json['batches']) == 2

    # check the 2nd batch, that updated core data without states
    assert resp.json['batches'][1]['batchId'] == 2
    assert len(resp.json['batches'][1]['coreData']) == 2
    # spot-check a few values
    assert resp.json['batches'][1]['coreData'][0]['state'] == 'AK'
    assert resp.json['batches'][1]['coreData'][0]['positive'] == 709

    # try inserting unknown states
    payload['coreData'][0]['state'] = 'FOO'
    resp = client.post("/api/v1/batches",
                   data=json.dumps(payload),
                   content_type='application/json',
                   headers=headers)
    assert resp.status_code == 500
    # should we handle partial state update through batches endpoint?


def test_get_batches(app):
    with app.app_context():
        # write 2 batches
        bat1 = Batch(batchNote='test1', createdAt=datetime.datetime.now() ,
            isPublished=False, isRevision=False)
        bat2 = Batch(batchNote='test2', createdAt=datetime.datetime.now() ,
            isPublished=False, isRevision=False)
        db.session.add(bat1)
        db.session.add(bat2)
        db.session.commit()

    client = app.test_client()
    resp = client.get('/api/v1/batches')
    assert resp.status_code == 200
    assert len(resp.json['batches']) == 2
    batch_notes = {x['batchNote'] for x in resp.json['batches']}
    assert batch_notes == {'test1', 'test2'}

    # get batch by ID
    resp = client.get('/api/v1/batches/1')
    assert resp.status_code == 200
    assert resp.json['batchId'] == 1
    assert resp.json['batchNote'] == 'test1'


def test_publish_batch(app, headers, requests_mock):
    with app.app_context():
        # write 2 batches
        bat1 = Batch(batchNote='test1', createdAt=datetime.datetime.now() ,
            isPublished=False, isRevision=False)
        bat2 = Batch(batchNote='test2', createdAt=datetime.datetime.now() ,
            isPublished=False, isRevision=False)
        db.session.add(bat1)
        db.session.add(bat2)
        db.session.commit()

    client = app.test_client()
    resp = client.get('/api/v1/batches')
    assert resp.status_code == 200
    assert len(resp.json['batches']) == 2
    # check that both batches not published
    for batch in resp.json['batches']:
        assert batch['isPublished'] == False

    # ensure the webhook is called on publish
    webhook_url = 'http://example.com/web/hook'
    app.config['API_WEBHOOK_URL'] = webhook_url
    requests_mock.get(webhook_url, json={'it': 'worked'})

    # publish the 2nd batch
    resp = client.post('/api/v1/batches/2/publish', headers=headers)
    assert resp.status_code == 201
    # this should've returned the published batch
    assert resp.json['batchId'] == 2
    assert resp.json['isPublished'] == True
    assert requests_mock.call_count == 1

    # check that the GET requests correctly reflect published status
    assert client.get('/api/v1/batches/1').json['isPublished'] == False
    assert client.get('/api/v1/batches/2').json['isPublished'] == True


def test_any_existing_rows(app, headers):
    client = app.test_client()

    # Write a batch containing the above data, one day for NY and WA
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(daily_push_ny_wa_yesterday()),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']

    # Publish the new batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id), headers=headers)
    assert resp.status_code == 201

    # Write a batch for today but don't publish it yet
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(daily_push_ny_wa_today()),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']

    # there should be existing published rows for yesterday NY and WA, and nothing else
    with app.app_context():
        assert any_existing_rows('NY', YESTERDAY.strftime("%Y%m%d"))
        assert any_existing_rows('WA', YESTERDAY.strftime("%Y%m%d"))
        assert not any_existing_rows('ZZ', YESTERDAY.strftime("%Y%m%d"))
        assert not any_existing_rows('NY', TODAY.strftime("%Y%m%d"))

    # Publish today's batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id), headers=headers)
    assert resp.status_code == 201

    # there should be existing published rows for yesterday and today NY and WA
    with app.app_context():
        assert any_existing_rows('NY', YESTERDAY.strftime("%Y%m%d"))
        assert any_existing_rows('WA', YESTERDAY.strftime("%Y%m%d"))
        assert any_existing_rows('NY', TODAY.strftime("%Y%m%d"))
        assert any_existing_rows('WA', TODAY.strftime("%Y%m%d"))
        assert not any_existing_rows('ZZ', YESTERDAY.strftime("%Y%m%d"))


def test_push_with_validation_error(app, headers, slack_mock):
    client = app.test_client()

    # string in a numeric field
    bad_data = daily_push_ny_wa_today()
    bad_data["coreData"][0]["negative"] = "this is a string"
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(bad_data),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 400
    resp_data = resp.data.decode("utf-8")
    assert "Non-numeric value for field" in resp_data
    assert 'NY ' in resp_data
    assert slack_mock.files_upload.call_count == 1

    # negative number in a numeric field
    bad_data = daily_push_ny_wa_today()
    bad_data["coreData"][0]["negative"] = -3
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(bad_data),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 400
    resp_data = resp.data.decode("utf-8")
    assert "Negative value for field" in resp_data
    assert 'NY ' in resp_data
    assert slack_mock.files_upload.call_count == 2

    # empty value for non-nullable field
    bad_data = daily_push_ny_wa_today()
    bad_data["coreData"][0]["state"] = None
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(bad_data),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 400
    resp_data = resp.data.decode("utf-8")
    assert "Missing value for 'state' in row" in resp_data
    assert slack_mock.files_upload.call_count == 3


def test_push_missing_context(app, headers, slack_mock):
    client = app.test_client()

    bad_data = daily_push_ny_wa_today()
    bad_data.pop("context")
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(bad_data),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 400
    assert "Payload requires 'context' field" in resp.data.decode("utf-8")
    assert slack_mock.files_upload.call_count == 1


def test_get_state_date_history(app, headers):
    client = app.test_client()

    # Write a batch containing the above data, two days for NY and WA, publish it
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(daily_push_ny_wa_two_days()),
        content_type='application/json',
        headers=headers)
    first_batch_id = resp.json['batch']['batchId']
    resp = client.post("/api/v1/batches/{}/publish".format(first_batch_id), headers=headers)

    # make (and implicitly publish) an edit batch for NY for yesterday, and leave today alone
    resp = client.post(
        "/api/v1/batches/edit_states_daily",
        data=json.dumps(edit_push_ny_yesterday_unchanged_today()),
        content_type='application/json',
        headers=headers)
    second_batch_id = resp.json['batch']['batchId']

    # get history for NY yesterday, should have two rows
    resp = client.get("/api/v1/state-date-history/NY/2020-05-24")
    assert len(resp.json) == 2
    assert resp.json[0]['batchId'] == second_batch_id  # most recent first
    assert resp.json[0]['positive'] == 16
    assert resp.json[0]['batch']['shiftLead'] == 'test'
    assert 'coreData' not in resp.json[0]['batch']

    assert resp.json[1]['batchId'] == first_batch_id
    assert resp.json[1]['positive'] == 15

    # history for NY today should have just one row
    resp = client.get("/api/v1/state-date-history/NY/2020-05-25")
    assert len(resp.json) == 1
