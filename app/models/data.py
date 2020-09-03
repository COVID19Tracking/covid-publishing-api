"""This is an example model which will be used for creating stories on the web.
The model is defined in a similar way to python class/object, however is
inherited from a SQLAlchemy class so a DB entry with a table can be built
easily
"""

import csv
from datetime import datetime, date
from dateutil import parser
import os
import pytz

from app import db
import logging

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import class_mapper, relationship


class DataMixin(object):

    def to_dict(self):
        d = {}
        # get column attributes, skip any nulls
        for column in self.__table__.columns:
            repr_fn = column.info.get("repr")
            attr = getattr(self, column.name)
            if attr is not None:
                if repr_fn is not None:
                    attr = repr_fn(attr)
                d[column.name] = attr
        # get derived fields (hybrid_property)
        for key, prop in inspect(self.__class__).all_orm_descriptors.items():
            if isinstance(prop, hybrid_property):
                d[key] = getattr(self, key)

        return d


class Batch(db.Model, DataMixin):
    __tablename__ = 'batches'

    # primary key
    batchId = db.Column(db.Integer, primary_key=True)

    createdAt = db.Column(db.DateTime(timezone=True), nullable=False)
    publishedAt = db.Column(db.DateTime(timezone=True))
    shiftLead = db.Column(db.String(100))
    batchNote = db.Column(db.String)
    dataEntryType = db.Column(db.String)

    logCategory = db.Column(db.String)
    link = db.Column(db.String)
    user = db.Column(db.String)

    # false if preview state, true if live
    isPublished = db.Column(db.Boolean, nullable=False)
    isRevision = db.Column(db.Boolean, nullable=False)

    coreData = relationship('CoreData', backref='batch')

    # This method isn't used when the object is read from the DB; only when a new one is being
    # created, as from a POST JSON payload.
    def __init__(self, **kwargs):
        # parse datetime fields

        # if there is no createdAt field, set it to datetime now
        if 'createdAt' not in kwargs:
            kwargs['createdAt'] = pytz.utc.localize(datetime.now())
        else:
            logging.info(
                'New batch came in with existing createdAt: %s' % kwargs['createdAt'])

        # setting default values for isPublished, isRevision: mimics preview state (if not set)
        if 'isPublished' not in kwargs:
            kwargs['isPublished'] = False
        if 'isRevision' not in kwargs:
            kwargs['isRevision'] = False

        mapper = class_mapper(Batch)
        relevant_kwargs = {k: v for k, v in kwargs.items() if k in mapper.attrs.keys()}
        super(Batch, self).__init__(**relevant_kwargs)


    def to_dict(self):
        d = super(Batch, self).to_dict()
        d['coreData'] = [coreData.to_dict() for coreData in self.coreData]
        return d


_FIPS_MAP = None
def fips_lookup(state):
    global _FIPS_MAP
    if _FIPS_MAP is None:
        # hack: load the fips lookup once
        path = os.path.join(os.path.dirname(__file__), 'fips-lookup.csv')
        _FIPS_MAP = {}
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                _FIPS_MAP[row['state']] = row['fips']
    return _FIPS_MAP[state]

class State(db.Model, DataMixin):
    __tablename__ = 'states'

    state = db.Column(db.String, primary_key=True, nullable=False)
    name = db.Column(db.String)
    covid19Site = db.Column(db.String)
    covid19SiteOld = db.Column(db.String)
    covid19SiteSecondary = db.Column(db.String)
    covid19SiteTertiary = db.Column(db.String)
    twitter = db.Column(db.String)
    notes = db.Column(db.String)
    pui = db.Column(db.String)
    covidTrackingProjectPreferredTotalTestUnits = db.Column(db.String)
    covidTrackingProjectPreferredTotalTestField = db.Column(db.String)

    # here for parity with public API, deprecated field
    @hybrid_property
    def pum(self):
        return False

    @hybrid_property
    def fips(self):
        return fips_lookup(self.state)

    def __init__(self, **kwargs):
        mapper = class_mapper(State)
        relevant_kwargs = {k: v for k, v in kwargs.items() if k in mapper.attrs.keys()}
        super(State, self).__init__(**relevant_kwargs)


class CoreData(db.Model, DataMixin):
    __tablename__ = 'coreData'

    # composite PK: state_name, batch_id, date
    state = db.Column(db.String, db.ForeignKey('states.state'), 
        nullable=False, primary_key=True)
    batchId = db.Column(db.Integer, db.ForeignKey('batches.batchId'),
        nullable=False, primary_key=True)
    # the day we mean to report this data for; meant for "states daily" extraction
    date = db.Column(db.Date, nullable=False, primary_key=True,
        info={'repr': lambda x: x.strftime('%Y-%m-%d')})

    # data columns
    positive = db.Column(db.Integer, info={"includeInUSDaily": True})
    negative = db.Column(db.Integer, info={"includeInUSDaily": True})
    pending = db.Column(db.Integer, info={"includeInUSDaily": True})
    hospitalizedCurrently = db.Column(db.Integer, info={"includeInUSDaily": True})
    hospitalizedCumulative = db.Column(db.Integer, info={"includeInUSDaily": True})
    inIcuCurrently = db.Column(db.Integer, info={"includeInUSDaily": True})
    inIcuCumulative = db.Column(db.Integer, info={"includeInUSDaily": True})
    onVentilatorCurrently = db.Column(db.Integer, info={"includeInUSDaily": True})
    onVentilatorCumulative = db.Column(db.Integer, info={"includeInUSDaily": True})
    recovered = db.Column(db.Integer, info={"includeInUSDaily": True})
    death = db.Column(db.Integer, info={"includeInUSDaily": True})
    deathConfirmed = db.Column(db.Integer, info={"includeInUSDaily": True})
    deathProbable = db.Column(db.Integer, info={"includeInUSDaily": True})
    positiveConfirmed = db.Column(db.Integer, info={"includeInUSDaily": True})
    probableCases = db.Column(db.Integer, info={"includeInUSDaily": True})

    # PCR/viral fields
    totalTestsViral = db.Column(db.Integer, info={"includeInUSDaily": True})
    positiveTestsViral = db.Column(db.Integer, info={"includeInUSDaily": True})
    negativeTestsViral = db.Column(db.Integer, info={"includeInUSDaily": True})
    positiveCasesViral = db.Column(db.Integer, info={"includeInUSDaily": True})
    totalTestEncountersViral = db.Column(db.Integer, info={"includeInUSDaily": True})
    totalTestsPeopleViral = db.Column(db.Integer, info={"includeInUSDaily": True})

    # Antibody fields
    totalTestsAntibody = db.Column(db.Integer, info={"includeInUSDaily": True})
    positiveTestsAntibody = db.Column(db.Integer, info={"includeInUSDaily": True})
    negativeTestsAntibody = db.Column(db.Integer, info={"includeInUSDaily": True})
    positiveTestsPeopleAntibody = db.Column(db.Integer, info={"includeInUSDaily": True})
    negativeTestsPeopleAntibody = db.Column(db.Integer, info={"includeInUSDaily": True})
    totalTestsPeopleAntibody = db.Column(db.Integer, info={"includeInUSDaily": True})

    # Antigen testing
    totalTestsPeopleAntigen = db.Column(db.Integer, info={"includeInUSDaily": True})
    positiveTestsPeopleAntigen = db.Column(db.Integer, info={"includeInUSDaily": True})
    negativeTestsPeopleAntigen = db.Column(db.Integer, info={"includeInUSDaily": True})
    totalTestsAntigen = db.Column(db.Integer, info={"includeInUSDaily": True})
    positiveTestsAntigen = db.Column(db.Integer, info={"includeInUSDaily": True})
    negativeTestsAntigen = db.Column(db.Integer, info={"includeInUSDaily": True})

    # from worksheet, "Notes" column (made by checker or doublechecker)
    privateNotes = db.Column(db.String)
    # Public Notes related to state
    notes = db.Column(db.String)

    # these are the source-of-truth time columns in UTC/GMT. String representations are in UTC.
    lastUpdateTime = db.Column(db.DateTime(timezone=True),
        info={'repr': lambda x: x.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    dateChecked = db.Column(db.DateTime(timezone=True),
        info={'repr': lambda x: x.astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
    
    checker = db.Column(db.String(100))
    doubleChecker = db.Column(db.String(100))
    publicNotes = db.Column(db.String)

    dataQualityGrade = db.Column(db.String)

    # TODO: which columns from state matrix and states? In general, what metadata?
    # What other columns are we missing?
    sourceNotes = db.Column(db.String)

    # Returns a list of CoreData column names representing numerical data that needs to be summed
    # and served in States Daily.
    @classmethod
    def numeric_fields(cls):
        colnames = []
        for column in cls.__table__.columns:
            if column.info.get("includeInUSDaily") == True:
                colnames.append(column.name)

        return colnames

    @hybrid_property
    def lastUpdateEt(self):
        # convert lastUpdateTime (UTC) to ET, return a string that matches how we're outputting
        # in the public API
        if self.lastUpdateTime is not None:
            return self.lastUpdateTime.astimezone(pytz.timezone('US/Eastern')).strftime(
                "%-m/%-d/%Y %H:%M")
        else:
            return None

    @hybrid_property
    def totalTestResults(self):
        # Calculated value (positive + negative) of total test results.
        # For consistency with public API, treating a negative null as 0
        if self.negative is None:
            return self.positive or 0
        if self.positive is None:
            return self.negative or 0
        return self.positive + self.negative

    # Converts the input to a string and returns parsed datetime.date object
    @staticmethod
    def parse_str_to_date(date_input):
        return parser.parse(str(date_input), ignoretz=True).date()

    def __init__(self, **kwargs):
        # strip any empty string fields from kwargs
        kwargs = {k: v for k, v in kwargs.items() if v is not None and v != ""}

        # accept either lastUpdateTime or lastUpdateIsoUtc as an input
        last_update_str = kwargs.get('lastUpdateTime') or kwargs.get('lastUpdateIsoUtc')
        if last_update_str:
            last_update_time = parser.parse(last_update_str)
            if last_update_time.tzinfo is None:
                raise ValueError(
                    'Expected a timezone with last update time: %s' % last_update_str)
            kwargs['lastUpdateTime'] = last_update_time

        if 'dateChecked' in kwargs:
            date_checked = parser.parse(kwargs['dateChecked'])
            if date_checked.tzinfo is None:
                raise ValueError(
                    'Expected a timezone with dateChecked: %s' % kwargs['dateChecked'])
            kwargs['dateChecked'] = date_checked

        # "date" is expected to be a date string, no times or timezones
        if 'date' in kwargs:
            kwargs['date'] = self.parse_str_to_date(kwargs['date'])
        else:
            kwargs['date'] = date.today()

        mapper = class_mapper(CoreData)
        relevant_kwargs = {k: v for k, v in kwargs.items() if k in mapper.attrs.keys()}
        super(CoreData, self).__init__(**relevant_kwargs)
