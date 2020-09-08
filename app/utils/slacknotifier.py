"""Notify Slack about errors and publishing events"""
import traceback

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


def notify_slack(message, file_attachment=None):
    """Send `message` to the Slack channel configured in the environment config

    Args:
        message (str): message to be sent to Slack
        file_attachment (str): optional file to be attached to the message inside a thread
    """
    try:
        if should_call_slack():
            response = client().chat_postMessage(
                channel=channel(),
                text=message
            )

            # send the attachment, if present, as a thread to the initial message
            if file_attachment is not None and response.validate() and response.get("ts") is not None:
                client().files_upload(
                    channels=channel(),
                    thread_ts=response.get("ts"),
                    content=file_attachment,
                    filetype='text',
                    title='Changes',
                    initial_comment=f":ctp-eye:"
                )
    except SlackApiError as e:
        # just log Slack failures but don't break on them
        current_app.logger.error(e.response["error"])


def notify_slack_error(message, source):
    """Send error message `message` to the Slack channel configured in the environment config.
    The error is delivered to Slack as a file for visual distinctiveness and to provide an expanding
    view for long exceptions without cluttering the channel.
    Args:
        message (str): Error message
        source (str): The operation or API endpoint causing the error (e.g. `post_core_data`)
    """
    try:
        if should_call_slack():
            client().files_upload(
                channels=channel(),
                content=message,
                filetype='text',
                title='Error details',
                initial_comment=f"*:rotating_light: Error in {source}*"
            )
    except SlackApiError as slack_error:
        current_app.logger.error(slack_error.response["error"])


def exceptions_to_slack(function):
    """A decorator that catches any exceptions from the passed in function
    and sends them to Slack before re-raising them. This allows us to control
    what endpoints report errors to Slack."""

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as e:
            notify_slack_error(traceback.format_exc(), function.__name__)
            raise e  # raise the original exception again

    return wrapper
