"""
Edit testing for V1 of API
"""
from flask import json, jsonify

from app import db
from app.api.data import any_existing_rows
from app.models.data import *
from common import *
import datetime


def test_edit_state_metadata(app, headers, requests_mock):
    client = app.test_client()

    # write some initial data
    example_filename = os.path.join(os.path.dirname(__file__), 'data.json')
    with open(example_filename) as f:
        payload_json_str = f.read()

    resp = client.post(
        "/api/v1/batches",
        data=payload_json_str,
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201

    # we should've written 56 states, 4 core data rows, 1 batch
    resp = client.get('/api/v1/public/states/info')
    assert len(resp.json) == 56
    assert resp.json[0]['state'] == "AK"
    assert resp.json[0]['twitter'] == "@Alaska_DHSS"

    # make a states metadata edit request updating the twitter account for AK
    state_data = {
        'states': [{
            'state': 'AK',
            'twitter': 'AlaskaNewTwitter'
        }]
    }
    # ensure the webhook is called on edit
    webhook_url = 'http://example.com/web/hook'
    app.config['API_WEBHOOK_URL'] = webhook_url
    requests_mock.get(webhook_url, json={'it': 'worked'})
    resp = client.post(
        "/api/v1/states/edit",
        data=json.dumps(state_data),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    assert len(resp.json['states']) == 1
    assert resp.json['states'][0]['state'] == "AK"
    assert resp.json['states'][0]['twitter'] == "AlaskaNewTwitter"
    assert requests_mock.call_count == 1


def test_edit_core_data(app, headers, slack_mock, requests_mock):
    client = app.test_client()

    # Write a batch containing the above data, two days for NY and WA, publish it
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(daily_push_ny_wa_two_days()),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']
    assert slack_mock.chat_postMessage.call_count == 1

    # Publish the new batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id), headers=headers)
    assert resp.status_code == 201
    assert slack_mock.chat_postMessage.call_count == 2

    # make an edit batch for NY for yesterday
    # ensure the webhook is called on edit
    webhook_url = 'http://example.com/web/hook'
    app.config['API_WEBHOOK_URL'] = webhook_url
    requests_mock.get(webhook_url, json={'it': 'worked'})
    resp = client.post(
        "/api/v1/batches/edit",
        data=json.dumps(edit_push_ny_yesterday()),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    assert slack_mock.chat_postMessage.call_count == 3
    assert requests_mock.call_count == 1
    batch_id = resp.json['batch']['batchId']
    assert resp.json['batch']['user'] == 'testing'

    # test that getting the states daily for NY has the UNEDITED data for yesterday
    resp = client.get("/api/v1/public/states/NY/daily")
    assert len(resp.json) == 2
    unedited = resp.json

    for day_data in resp.json:
        assert day_data['date'] in ['2020-05-25', '2020-05-24']
        if day_data['date'] == '2020-05-25':
            assert day_data['positive'] == 20
            assert day_data['negative'] == 5
        elif day_data['date'] == '2020-05-24':
            assert day_data['positive'] == 15
            assert day_data['negative'] == 4

    # Publish the edit batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id), headers=headers)
    assert resp.status_code == 201

    # test that getting the states daily for NY has the edited data for yesterday
    resp = client.get("/api/v1/public/states/NY/daily")
    assert len(resp.json) == 2

    for day_data in resp.json:
        assert day_data['date'] in ['2020-05-25', '2020-05-24']
        if day_data['date'] == '2020-05-25':
            assert day_data['positive'] == 20
            assert day_data['negative'] == 5
        elif day_data['date'] == '2020-05-24':
            assert day_data['positive'] == 16
            assert day_data['negative'] == 4

def test_edit_core_data_from_states_daily_empty(app, headers, slack_mock, requests_mock):
    client = app.test_client()

    # Write a batch containing the above data, two days for NY and WA, publish it
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(daily_push_ny_wa_two_days()),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']
    assert slack_mock.chat_postMessage.call_count == 1

    # Publish the new batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id), headers=headers)
    assert resp.status_code == 201
    assert slack_mock.chat_postMessage.call_count == 2

    # make an empty edit batch for NY for yesterday containing no edits
    # ensure the webhook is not called because the edit fails
    webhook_url = 'http://example.com/web/hook'
    app.config['API_WEBHOOK_URL'] = webhook_url
    requests_mock.get(webhook_url, json={'it': 'worked'})
    resp = client.post(
        "/api/v1/batches/edit_states_daily",
        data=json.dumps(edit_push_ny_today_empty()),
        content_type='application/json',
        headers=headers)

    assert resp.status_code == 400
    assert slack_mock.chat_postMessage.call_count == 2  # logging unchanged edit to Slack
    assert requests_mock.call_count == 0  # should not call the webhook
    assert "no edits detected" in resp.data.decode("utf-8")


def test_edit_core_data_from_states_daily(app, headers, slack_mock, requests_mock):
    client = app.test_client()

    # Write a batch containing the above data, two days for NY and WA, publish it
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(daily_push_ny_wa_two_days()),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']
    assert slack_mock.chat_postMessage.call_count == 1

    # Publish the new batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id), headers=headers)
    assert resp.status_code == 201
    assert slack_mock.chat_postMessage.call_count == 2
    assert slack_mock.files_upload.call_count == 0

    # make an edit batch for NY for yesterday, and leave today alone
    # ensure the webhook is not called because the edit fails
    webhook_url = 'http://example.com/web/hook'
    app.config['API_WEBHOOK_URL'] = webhook_url
    requests_mock.get(webhook_url, json={'it': 'worked'})
    resp = client.post(
        "/api/v1/batches/edit_states_daily",
        data=json.dumps(edit_push_ny_yesterday_unchanged_today()),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    assert slack_mock.chat_postMessage.call_count == 3
    assert slack_mock.files_upload.call_count == 1
    assert requests_mock.call_count == 1
    assert "state: NY" in slack_mock.chat_postMessage.call_args[1]['text']
    assert "Rows edited: 1" in slack_mock.files_upload.call_args[1]['content']
    assert "NY 2020-05-24" in slack_mock.files_upload.call_args[1]['content']
    assert "positive: 16 (was 15)" in slack_mock.files_upload.call_args[1]['content']
    assert "inIcuCurrently: None (was 37)" in slack_mock.files_upload.call_args[1]['content']

    batch_id = resp.json['batch']['batchId']
    assert resp.json['batch']['user'] == 'testing'
    # we've changed positive and removed inIcuCurrently, so both should count as changed
    assert len(resp.json['changedFields']) == 2
    assert 'positive' in resp.json['changedFields']
    assert 'inIcuCurrently' in resp.json['changedFields']
    assert resp.json['changedDates'] == '5/24/20'

    # confirm that the edit batch only contains one row with yesterday's data
    with app.app_context():
        batch_obj = Batch.query.get(batch_id)
        assert len(batch_obj.coreData) == 1
        assert batch_obj.coreData[0].date == datetime.date(2020,5,24)
        assert batch_obj.coreData[0].state == 'NY'
        assert batch_obj.link == 'https://example.com'
        assert batch_obj.user == 'testing'
        assert batch_obj.logCategory == 'State Updates'

        # make sure metadata got saved correctly also. This should match the above test cases
        # in the returned JSON
        assert 'positive' in batch_obj.changedFields
        assert 'inIcuCurrently' in batch_obj.changedFields
        assert batch_obj.changedDatesMin == datetime.date(2020,5,24)
        assert batch_obj.changedDatesMax == datetime.date(2020,5,24)
        assert batch_obj.numRowsEdited == 1

    # getting the states daily for NY has the edited data for yesterday and unchanged for today,
    # and the last batch should've been published as part of the "edit from states daily" endpoint
    resp = client.get("/api/v1/public/states/NY/daily")
    assert len(resp.json) == 2

    for day_data in resp.json:
        assert day_data['date'] in ['2020-05-25', '2020-05-24']
        if day_data['date'] == '2020-05-25':
            assert day_data['positive'] == 20
            assert day_data['negative'] == 5
            assert day_data['inIcuCurrently'] == 33
        elif day_data['date'] == '2020-05-24':
            assert day_data['positive'] == 16
            assert day_data['negative'] == 4
            # this value was blanked out in the edit, so it should be removed now
            assert 'inIcuCurrently' not in day_data

    # test editing 2 non-consecutive dates
    resp = client.post(
        "/api/v1/batches/edit_states_daily",
        data=json.dumps(edit_push_ny_today_and_before_yesterday()),
        content_type='application/json',
        headers=headers)
    assert resp.json['changedFields'] == ['inIcuCurrently']
    assert resp.json['changedDates'] == '5/20/20 - 5/25/20'
    assert resp.json['numRowsEdited'] == 2
    assert resp.json['user'] == 'testing'

    # check to see if the row for the new date (BEFORE_YESTERDAY) was added
    resp = client.get("/api/v1/public/states/NY/daily")
    found_new_date = False
    for day_data in resp.json:
        if day_data['date'] == '2020-05-20':
            found_new_date = True
            assert day_data['positive'] == 10
            assert day_data['negative'] == 2
    assert found_new_date is True

    # the slack notification should note the addition of the new row
    assert "New rows: 1" in slack_mock.files_upload.call_args[1]['content']
    assert "NY 2020-05-20" in slack_mock.files_upload.call_args[1]['content']

    # test that sending an edit batch with multiple states fails
    resp = client.post(
        "/api/v1/batches/edit_states_daily",
        data=json.dumps(edit_push_multiple_states()),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 400

    # test that sending an edit batch with no CoreData rows fails
    bad_data = edit_push_multiple_states()
    bad_data['coreData'] = []
    resp = client.post(
        "/api/v1/batches/edit_states_daily",
        data=json.dumps(bad_data),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 400


def test_edit_core_data_from_states_daily_timestamps_only(app, headers, slack_mock):
    client = app.test_client()

    # Write a batch containing the above data, two days for NY and WA, publish it
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(daily_push_ny_wa_two_days()),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']
    assert slack_mock.chat_postMessage.call_count == 1

    # Publish the new batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id), headers=headers)
    assert resp.status_code == 201
    assert slack_mock.chat_postMessage.call_count == 2

    # make an edit batch for NY for yesterday, and leave today alone
    resp = client.post(
        "/api/v1/batches/edit_states_daily",
        data=json.dumps(edit_push_ny_yesterday_change_only_timestamp()),
        content_type='application/json',
        headers=headers)

    assert resp.status_code == 201
    assert slack_mock.chat_postMessage.call_count == 3
    assert "state: NY" in slack_mock.chat_postMessage.call_args[1]['text']
    batch_id = resp.json['batch']['batchId']
    assert resp.json['batch']['user'] == 'testing'
    # we've changed only lastUpdateIsoUtc, which is lastUpdateTime on output
    assert len(resp.json['changedFields']) == 1
    assert 'lastUpdateTime' in resp.json['changedFields']


def test_edit_core_data_from_states_daily_partial_update(app, headers, slack_mock):
    ''' Verify that when sending only part of the fileds, then these fields
    are updated, and the other are set with the most recent published
    batch values
    '''

    # setup
    client = app.test_client()

    # prep
    # Write a batch containing the above data, two days for NY and WA, publish it
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(daily_push_ny_wa_two_days()),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']
    assert slack_mock.chat_postMessage.call_count == 1

    # Publish the new batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id), headers=headers)
    assert resp.status_code == 201
    assert slack_mock.chat_postMessage.call_count == 2

    # test
    # make an edit batch for NY for yesterday, and leave today alone
    resp = client.post(
        "/api/v1/batches/edit_states_daily",
        data=json.dumps(edit_push_ny_yesterday_change_only_positive()),
        content_type='application/json',
        headers=headers)

    # verify
    assert resp.status_code == 201
    assert slack_mock.chat_postMessage.call_count == 3
    assert "state: NY" in slack_mock.chat_postMessage.call_args[1]['text']
    batch_id = resp.json['batch']['batchId']
    assert resp.json['batch']['user'] == 'testing'
    # submitted a single field, and that's the only field that should change
    assert len(resp.json['changedFields']) == 1
    assert 'positive' in resp.json['changedFields']

    # test that getting the states daily for NY has the UNEDITED data for yesterday
    resp = client.get("/api/v1/public/states/NY/daily")
    assert len(resp.json) == 2
    yesterday = resp.json[1]
    assert yesterday['date'] == '2020-05-24'
    assert yesterday['positive'] == 16
    assert yesterday['negative'] == 4
    assert yesterday['inIcuCurrently'] == 37

    # test
    # make exactly the same edit
    resp = client.post(
        "/api/v1/batches/edit_states_daily",
        data=json.dumps(edit_push_ny_yesterday_change_only_positive()),
        content_type='application/json',
        headers=headers)

    # verify
    assert resp.status_code == 400
    assert slack_mock.chat_postMessage.call_count == 3
    assert "no edits detected" in resp.data.decode("utf-8")

def test_edit_with_valid_and_unknown_fields(app, headers, slack_mock):
    ''' Verify that when sending edit (or insert) requests without any fields
    that are part of the object the edit requests is rejected
    '''

    # setup
    client = app.test_client()

    # prep
    # Write a batch containing data for NY, WA for 2 days
    resp = client.post(
        "/api/v1/batches",
        data=json.dumps(daily_push_ny_wa_two_days()),
        content_type='application/json',
        headers=headers)
    assert resp.status_code == 201
    batch_id = resp.json['batch']['batchId']
    assert slack_mock.chat_postMessage.call_count == 1

    # Publish the new batch
    resp = client.post("/api/v1/batches/{}/publish".format(batch_id), headers=headers)
    assert resp.status_code == 201
    assert slack_mock.chat_postMessage.call_count == 2

    # test
    # make an edit batch without any significant field
    resp = client.post(
        "/api/v1/batches/edit_states_daily",
        data=json.dumps(edit_unknown_fields()),
        content_type='application/json',
        headers=headers)

    # verify: nothing was edited
    assert resp.status_code == 400
    assert slack_mock.chat_postMessage.call_count == 2
    assert "no edits detected" in resp.data.decode("utf-8")
