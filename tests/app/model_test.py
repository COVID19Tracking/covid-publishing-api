"""
Tests for SQLAlchemy models
"""
import pytest

from flask import json, jsonify

from app import db
from app.models.data import *


def test_state_model():
    states_dict = {
        'state': 'WA', 'name': 'Washington',
    }
    state = State(**states_dict)
    assert state.state == 'WA'
    assert state.name == 'Washington'


def _add_test_data(context_db):
    nys = State(state='NY')
    bat = Batch(batchNote='test', createdAt=datetime.now(),
        isPublished=False, isRevision=False)
    context_db.session.add(bat)
    context_db.session.add(nys)
    context_db.session.flush()

    core_data_row = CoreData(
        lastUpdateIsoUtc=datetime.now().isoformat(),
        date=datetime.today(), state='NY', batchId=bat.batchId,
        positive=20, negative=5)
    
    context_db.session.add(core_data_row)
    context_db.session.commit()


def test_core_data_model(app):
    with app.app_context():
        _add_test_data(db)

        states = State.query.all()
        assert len(states) == 1
        state = states[0]
        assert state.state == 'NY'
        assert state.to_dict() == {'state': 'NY'}

        batches = Batch.query.all()
        assert len(batches) == 1
        batch = batches[0]
        assert batch.batchId == 1

        core_data_all = CoreData.query.all()
        assert len(core_data_all) == 1
        core_data_row = core_data_all[0]
        assert core_data_row.batchId == batch.batchId
        assert core_data_row.state == state.state

        # check derived values
        assert core_data_row.totalTestResults == 25
        assert core_data_row.lastUpdateEt.tzinfo.zone == 'US/Eastern'
        
        # check that the Batch object is attached to this CoreData object
        assert core_data_row.batch == batch
        # also check the relationship in the other direction, that CoreData is attached to the batch
        assert len(batch.coreData) == 1
        assert batch.coreData[0] == core_data_row


