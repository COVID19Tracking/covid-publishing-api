"""This is an example model which will be used for creating stories on the web.
The model is defined in a similar way to python class/object, however is
inherited from a SQLAlchemy class so a DB entry with a table can be built
easily
"""

from datetime import datetime, date
from dateutil import parser
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
            attr = getattr(self, column.name)
            if attr is not None:
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

        # setting default values for isPublished, isRevision: mimics preview state
        kwargs['isPublished'] = False
        kwargs['isRevision'] = False

        mapper = class_mapper(Batch)
        relevant_kwargs = {k: v for k, v in kwargs.items() if k in mapper.attrs.keys()}
        super(Batch, self).__init__(**relevant_kwargs)


    def to_dict(self):
        d = super(Batch, self).to_dict()
        d['coreData'] = [coreData.to_dict() for coreData in self.coreData]
        return d


class State(db.Model, DataMixin):
    __tablename__ = 'states'

    state = db.Column(db.String, primary_key=True, nullable=False)
    name = db.Column(db.String)
    covid19Site = db.Column(db.String)
    covid19SiteOld = db.Column(db.String)
    covid19SiteSecondary = db.Column(db.String)
    twitter = db.Column(db.String)
    notes = db.Column(db.String)
    pui = db.Column(db.String)
    pum = db.Column(db.Boolean)
    fips = db.Column(db.String)

    def __init__(self, **kwargs):
        mapper = class_mapper(State)
        relevant_kwargs = {k: v for k, v in kwargs.items() if k in mapper.attrs.keys()}
        super(State, self).__init__(**relevant_kwargs)


class CoreData(db.Model, DataMixin):
    __tablename__ = 'coreData'

    # composite PK: state_name, batch_id
    state = db.Column(db.String, db.ForeignKey('states.state'), 
        nullable=False, primary_key=True)
    batchId = db.Column(db.Integer, db.ForeignKey('batches.batchId'),
        nullable=False, primary_key=True)

    # data columns
    positive = db.Column(db.Integer)
    negative = db.Column(db.Integer)
    pending = db.Column(db.Integer)
    hospitalizedCurrently = db.Column(db.Integer)
    hospitalizedCumulative = db.Column(db.Integer)
    inIcuCurrently = db.Column(db.Integer)
    inIcuCumulative = db.Column(db.Integer)
    onVentilatorCurrently = db.Column(db.Integer)
    onVentilatorCumulative = db.Column(db.Integer)
    recovered = db.Column(db.Integer)
    death = db.Column(db.Integer)
    deathConfirmed = db.Column(db.Integer)
    deathProbable = db.Column(db.Integer)
    antibodyTotal = db.Column(db.Integer)
    antibodyPositive = db.Column(db.Integer)
    antibodyNegative = db.Column(db.Integer)
    pcrTotalTests = db.Column(db.Integer)
    pcrPositiveTests = db.Column(db.Integer)
    pcrNegativeTests = db.Column(db.Integer)
    pcrPositiveCases = db.Column(db.Integer)
    totalTestsPeople = db.Column(db.Integer)
    positiveConfirmed = db.Column(db.Integer)

    # from worksheet, "Notes" column (made by checker or doublechecker)
    privateNotes = db.Column(db.String)
    # Public Notes related to state
    notes = db.Column(db.String)

    lastUpdateTime = db.Column(db.DateTime(timezone=True), nullable=False)
    dateChecked = db.Column(db.DateTime(timezone=True), nullable=False)

    # the day we mean to report this data for; meant for "states daily" extraction
    dataDate = db.Column(db.Date, nullable=False)
    checker = db.Column(db.String(100))
    doubleChecker = db.Column(db.String(100))
    publicNotes = db.Column(db.String)

    # TODO: which columns from state matrix and states? In general, what metadata?
    # What other columns are we missing?
    sourceNotes = db.Column(db.String)

    # TODO: add key that ensures (state, batchId, date) is unique in coreData, so there can't be any
    # ambiguity if there are somehow duplicates in a batch

    @hybrid_property
    def lastUpdateEt(self):
        # convert lastUpdateTime (UTC) to ET
        return self.lastUpdateTime.astimezone(pytz.timezone('US/Eastern'))

    @hybrid_property
    def checkTimeEt(self):
        # convert dateChecked (UTC) to ET
        return self.dateChecked.astimezone(pytz.timezone('US/Eastern'))

    @hybrid_property
    def totalTestResults(self):
        # Calculated value (positive + negative) of total test results.
        # For consistency with public API, treating a negative null as 0
        if self.negative is None:
            return self.positive
        return self.positive + self.negative

    def __init__(self, **kwargs):
        # strip any empty string fields from kwargs
        kwargs = {k: v for k, v in kwargs.items() if v is not None and v != ""}

        # convert lastUpdateIsoUtc to lastUpdateTime
        kwargs['lastUpdateTime'] = parser.parse(kwargs['lastUpdateIsoUtc'])

        # FOR NOW defaulting dateChecked to lastUpdateTime; NEED TO FIX
        # ALSO FOR NOW defaulting "date" to today
        kwargs['dateChecked'] = kwargs['lastUpdateTime']
        kwargs['dataDate'] = date.today()

        mapper = class_mapper(CoreData)
        relevant_kwargs = {k: v for k, v in kwargs.items() if k in mapper.attrs.keys()}
        super(CoreData, self).__init__(**relevant_kwargs)
