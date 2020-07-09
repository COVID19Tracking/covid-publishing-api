import pytest
from app.utils.slacknotifier import *

def test_slack(app, slack_mock):
    with app.app_context():
        app.config["SLACK_API_TOKEN"] = None
        app.config["SLACK_CHANNEL"] = None

        # shouldn't do anything unless the config variables are set
        assert not should_call_slack()
        notify_slack("test")
        assert slack_mock.chat_postMessage.call_count == 0

        app.config["SLACK_API_TOKEN"] = "token"
        app.config["SLACK_CHANNEL"] = "channel"
        notify_slack("test")
        assert slack_mock.chat_postMessage.call_count == 1

        notify_slack_error("missing context", "post_core_data")
        assert slack_mock.files_upload.call_count == 1

        # trigger a a function that raises an exception and ensure slack is notified
        @exceptions_to_slack
        def error_function():
            return 42 / 0
        with pytest.raises(ZeroDivisionError):
            error_function()
        assert slack_mock.files_upload.call_count == 2
