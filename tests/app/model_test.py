"""
Tests for SQLAlchemy models
"""
from datetime import datetime
import pytest
import pytz

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


def test_core_data_model(app):
    with app.app_context():
        nys = State(state='NY')
        bat = Batch(batchNote='test', createdAt=datetime.now(),
            isPublished=False, isRevision=False)
        db.session.add(bat)
        db.session.add(nys)
        db.session.flush()

        now_utc = datetime(2020, 5, 4, 20, 3, tzinfo=pytz.UTC)
        core_data_row = CoreData(
            lastUpdateIsoUtc=now_utc.isoformat(), dateChecked=now_utc.isoformat(),
            date=datetime.today(), state='NY', batchId=bat.batchId,
            positive=20, negative=5)

        db.session.add(core_data_row)
        db.session.commit()

        states = State.query.all()
        assert len(states) == 1
        state = states[0]
        assert state.state == 'NY'
        assert state.to_dict() == {'state': 'NY', 'fips': '36', 'pum': False}

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

        # doing this crazy thing because the offset between UTC and EST varies depending on the date
        hour_in_et = now_utc.astimezone(pytz.timezone('US/Eastern')).hour
        assert core_data_row.lastUpdateEt == '5/4/2020 %d:03' % hour_in_et

        # check that the Batch object is attached to this CoreData object
        assert core_data_row.batch == batch
        # also check the relationship in the other direction, that CoreData is attached to the batch
        assert len(batch.coreData) == 1
        assert batch.coreData[0] == core_data_row

def test_core_data_fields():
    '''This test tests the valid_fields_checker method in CoreData '''

    # There are some consts and assumptions here about what is a field and what isn't.
    # It's not read dynamically

    valid_fields = ['positive', 'negative']
    keys = ['state', 'date', 'batchId']
    unknown_fields = ['moonBaze', 'marsBase', 'kuiperBeltShield']

    valids, unknowns = CoreData.valid_fields_checker(valid_fields + keys + unknown_fields)
    assert set(valid_fields) == set(valids)
    assert set(unknown_fields) == set(unknowns)


    valids, unknowns = CoreData.valid_fields_checker(valid_fields + keys)
    assert set(valid_fields) == set(valids)
    assert len(unknowns) == 0

    valids, unknowns = CoreData.valid_fields_checker(keys)
    assert len(valids) == 0
    assert len(unknowns) == 0

def test_total_test_results(app):
    with app.app_context():
        now_utc = datetime(2020, 5, 4, 20, 3, tzinfo=pytz.UTC)
        core_data_row = CoreData(
            lastUpdateIsoUtc=now_utc.isoformat(), dateChecked=now_utc.isoformat(),
            date=datetime.today(), state='NY')

        assert core_data_row.totalTestResults == 0

        core_data_row.positive = 25
        assert core_data_row.totalTestResults == 25
        core_data_row.positive = None
        core_data_row.negative = 5
        assert core_data_row.totalTestResults == 5
        core_data_row.positive = 25
        assert core_data_row.totalTestResults == 30

        # RI and CO have special behavior (use totalTestEncountersViral)
        core_data_row = CoreData(
            lastUpdateIsoUtc=now_utc.isoformat(), dateChecked=now_utc.isoformat(),
            date=datetime.today(), state='RI', positive=25, negative=5, totalTestEncountersViral=33)
        assert core_data_row.totalTestResults == 33
        core_data_row.state = 'NY'
        assert core_data_row.totalTestResults == 30
        core_data_row.state = 'CO'
        assert core_data_row.totalTestResults == 33
        core_data_row.totalTestEncountersViral = None
        assert core_data_row.totalTestResults == 0

        # MA uses totalTestsViral
        core_data_row = CoreData(
            lastUpdateIsoUtc=now_utc.isoformat(), dateChecked=now_utc.isoformat(),
            date=datetime.today(), state='MA', positive=25, negative=5, totalTestEncountersViral=33, totalTestsViral=12)
        assert core_data_row.totalTestResults == 12
