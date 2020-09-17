"""Used to call out to an external webhook (i.e. the public API build tool)
 when publishing new data to the database. The webhook URL is set in the
 environment with the `API_WEBHOOK_URL` variable"""

import requests
from flask import current_app

def notify_webhook():
    # TODO: replace this with an annotation that checks that response and makes
    # a call only on a successful response from the method it annotates

    url = current_app.config['API_WEBHOOK_URL']
    if not url: # nothing to do for dev environments without a url set
        return

    try:
        response = requests.get(url)
    except Exception as e:
        current_app.logger.warning(
            'Request to webhook %s failed returned an error: %s' % (url, str(e)))
        return False

    if response.status_code != 200:
        # log an error but do not raise an exception
        # This method would usually run *after a commit*, as a best-effort
        # method, it should not fail a response to the user
        current_app.logger.error(
            'Request to webhook %s finished unsuccessfully: %s, the response is:\n%s'
            % (url, response.status_code, response.text))

    return response
