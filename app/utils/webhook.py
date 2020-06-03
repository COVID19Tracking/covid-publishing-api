"""Used to call out to an external webhook (i.e. the public API build tool)
 when publishing new data to the database. The webhook URL is set in the
 environment with the `API_WEBHOOK_URL` variable"""

import requests
from flask import current_app

def notify_webhook():
    url = current_app.config['API_WEBHOOK_URL']
    if not url: # nothing to do for dev environments without a url set
        return

    response = requests.get(url)

    if response.status_code != 200:
        raise requests.HTTPError(
            'Request to webhook %s returned an error %s, the response is:\n%s'
            % (url, response.status_code, response.text)
        )
    return response
