"""Used to call out to an external webhook (i.e. the public API build tool)
 when publishing new data to the database. The webhook URL is set in the
 environment with the `API_WEBHOOK_URL` variable"""
import functools
import requests
from flask import current_app

from app.utils.slacknotifier import notify_slack_error


def notify_webhook(func):
    """Notifies a webhook (defined in the config with "API_WEBHOOK_URL") if the function it wraps is successful.
    Used to kick off the public API build after data changes."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        value = func(*args, **kwargs)

        # notify the webhook unless the response has a non-default status code and that status code is not successful
        if not (type(value) == tuple and value[1] >= 300):
            do_notify_webhook()

        return value
    return wrapper


def do_notify_webhook():
    url = current_app.config['API_WEBHOOK_URL']
    if not url:  # nothing to do for dev environments without a url set
        return

    try:
        response = requests.get(url)
    except Exception as e:
        current_app.logger.warning(
            'Request to webhook %s failed returned an error: %s' % (url, str(e)))
        notify_slack_error(f"notify_webhook failed: #{str(e)}", "do_notify_webhook")
        return False

    if response.status_code != 200:
        # log an error but do not raise an exception
        # This method would usually run *after a commit*, as a best-effort
        # method, it should not fail a response to the user
        current_app.logger.error(
            'Request to webhook %s finished unsuccessfully: %s, the response is:\n%s'
            % (url, response.status_code, response.text))
        notify_slack_error(f"notify_webhook failed (#{response.status_code}): #{response.text}", "do_notify_webhook")

    return response
