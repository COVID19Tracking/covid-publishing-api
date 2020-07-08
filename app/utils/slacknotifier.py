"""Notify Slack about errors and publishing events"""

from slack import WebClient
from slack.errors import SlackApiError
from flask import current_app
import functools

def client():
    token = current_app.config["SLACK_API_TOKEN"]
    return WebClient(token=token)

def channel():
    return current_app.config["SLACK_CHANNEL"]

def should_call_slack():
    return current_app.config["SLACK_API_TOKEN"] and current_app.config["SLACK_CHANNEL"]

def notify_slack(message):
    try:
        if should_call_slack():
            client().chat_postMessage(
                channel=channel(),
                text=message
            )
    except SlackApiError as e:
        # just log Slack failures but don't break on them
        current_app.logger.error(e.response["error"])

def exceptions_to_slack(function):
    """A decorator that catches any exceptions from the passed in function
    and sends them to Slack before re-raising them. This allows us to control
    what endpoints report errors to Slack."""
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            try:
                if should_call_slack():
                    client().files_upload(
                        channels=channel(),
                        content=str(e),
                        filetype='text',
                        title='Error details',
                        initial_comment=f"*Error in {function.__name__}*"
                    )
            except SlackApiError as slack_error:
                current_app.logger.error(slack_error.response["error"])
            raise e  # raise the original exception again
    return wrapper
