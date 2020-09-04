import pytest
from app.utils.slacknotifier import *


def test_slack_noop(app, slack_mock):
    with app.app_context():
        app.config["SLACK_API_TOKEN"] = None
        app.config["SLACK_CHANNEL"] = None

        # shouldn't do anything unless the config variables are set
        assert not should_call_slack()
        notify_slack("test")
        assert slack_mock.chat_postMessage.call_count == 0
        assert slack_mock.files_upload.call_count == 0


def test_notify_slack(app, slack_mock):
    with app.app_context():
        app.config["SLACK_API_TOKEN"] = "token"
        app.config["SLACK_CHANNEL"] = "channel"
        notify_slack("test")
        assert slack_mock.chat_postMessage.call_count == 1
        assert slack_mock.files_upload.call_count == 0  # no file specified, so no file should be uploaded

        # test notify_slack with a file attachment
        notify_slack("test2", "this is a file")
        assert slack_mock.chat_postMessage.call_count == 2
        assert slack_mock.files_upload.call_count == 1
        assert "this is a file" == slack_mock.files_upload.call_args[1]['content']


def test_notify_slack_error(app, slack_mock):
    with app.app_context():
        notify_slack_error("missing context", "post_core_data")
        assert slack_mock.files_upload.call_count == 1
        assert "missing context" == slack_mock.files_upload.call_args[1]['content']


def test_slack_exceptions(app, slack_mock):
    with app.app_context():
        # trigger a a function that raises an exception and ensure slack is notified
        @exceptions_to_slack
        def error_function():
            return 42 / 0
        with pytest.raises(ZeroDivisionError):
            error_function()
        assert slack_mock.files_upload.call_count == 1
        assert "ZeroDivisionError" in slack_mock.files_upload.call_args[1]['content']
