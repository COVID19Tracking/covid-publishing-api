from datetime import datetime

import app.api.data

import flask
import json

from app import db
from app.models.data import Batch, CoreData, State


def backfill(input_file):
    flask.current_app.logger.info('Backfilling core data from %s' % input_file)

    # blow away all core data, states, batches
    CoreData.query.delete()
    State.query.delete()
    Batch.query.delete()

    db.session.commit()

    with open(input_file) as f:
        payload_json = json.load(f)
        json_out = app.api.data.post_core_data_json(payload_json)

        # publish backfill batch
        batch_id = json_out[0].json['batch']['batchId']
        flask.current_app.logger.info('Publishing batch %s' % batch_id)
        batch = Batch.query.get_or_404(batch_id)
        batch.isPublished = True
        batch.publishedAt = datetime.utcnow()   # set publish time to now
        db.session.add(batch)
        db.session.commit()

    flask.current_app.logger.info('Backfilling complete!')
