import pytest
import requests_mock
from flask import Response
from requests import HTTPError

from app.api import api
from app.utils.webhook import do_notify_webhook, notify_webhook


def test_do_notify_webhook(app, requests_mock, slack_mock):
    with app.app_context():
        url = 'http://example.com/web/hook'
        app.config['API_WEBHOOK_URL'] = url
        requests_mock.get(url, json= {'it': 'worked'})
        resp = do_notify_webhook()
        assert requests_mock.call_count == 1
        assert resp.json() == {'it': 'worked'}
        # nothing should be posted to slack for a successful operation
        assert slack_mock.chat_postMessage.call_count == 0
        assert slack_mock.files_upload.call_count == 0

        requests_mock.get(url, status_code=500)
        resp = do_notify_webhook()
        assert requests_mock.call_count == 2
        # error should be reported to slack
        assert slack_mock.files_upload.call_count == 1

        # try with a bad url/error in request
        requests_mock.register_uri('GET', url, exc=HTTPError),
        resp = do_notify_webhook()
        assert resp is False
        # error should be reported to slack
        assert slack_mock.files_upload.call_count == 2


def test_webhook_decorator(app, requests_mock, slack_mock):
    with app.app_context():
        url = 'http://example.com/web/hook'
        app.config['API_WEBHOOK_URL'] = url
        requests_mock.get(url, json= {'it': 'worked'})

        @api.route('/test_webhook', methods=['GET'])
        @notify_webhook
        def successful_function():
            return "blah blah", 201
        assert requests_mock.call_count == 0
        successful_function()
        assert requests_mock.call_count == 1
        assert slack_mock.files_upload.call_count == 0

        @api.route('/test_webhook_fail', methods=['GET'])
        def unsuccessful_function():
            return "blah blah", 500
        assert requests_mock.call_count == 1
        unsuccessful_function()
        # webhook should not be called because the operation failed
        assert requests_mock.call_count == 1
        assert slack_mock.files_upload.call_count == 0
