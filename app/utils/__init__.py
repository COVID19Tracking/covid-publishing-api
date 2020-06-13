"""Initiates utils through Flask's blueprint"""

from app.models.data import *
import app.api.data

import click
import flask
import json

utils = flask.Blueprint('utils', __name__)

@utils.cli.command('backfill')
@click.argument('input_file')
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
