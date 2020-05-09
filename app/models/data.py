"""This is an example model which will be used for creating stories on the web.
The model is defined in a similar way to python class/object, however is
inherited from a SQLAlchemy class so a DB entry with a table can be built
easily
"""

from datetime import datetime
from dateutil import tz

from app import db

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import relationship

class DataMixin(object):

    def to_dict(self):
        d = {}
        for column in self.__table__.columns:
            attr = getattr(self, column.name)
            if attr is not None:
                d[column.name] = attr
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

    def __init__(self, **kwargs):
        super(Batch, self).__init__(**kwargs)


class State(db.Model, DataMixin):
    __tablename__ = 'states'

    state = db.Column(db.String, primary_key=True, nullable=False)
    fullName = db.Column(db.String)

    def __init__(self, **kwargs):
        super(State, self).__init__(**kwargs)


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

    # from worksheet, "Notes" column (made by checker or doublechecker)
    privateNotes = db.Column(db.String)
    # Public Notes related to state
    notes = db.Column(db.String)

    lastUpdateTime = db.Column(db.DateTime(timezone=True), nullable=False)
    lastCheckTime = db.Column(db.DateTime(timezone=True), nullable=False)

    # the day we mean to report this data for; meant for "states daily" extraction
    date = db.Column(db.Date, nullable=False)
    checker = db.Column(db.String(100))
    doubleChecker = db.Column(db.String(100))
    publicNotes = db.Column(db.String)

    # TODO: which columns from state matrix and states? In general, what metadata?
    # What other columns are we missing?
    sourceNotes = db.Column(db.String)

    def __init__(self, **kwargs):
        super(CoreData, self).__init__(**kwargs)

    @hybrid_property
    def lastUpdateEt(self):
        # convert lastUpdateTime (UTC) to ET
        raise NotImplementedError

    @hybrid_property
    def checkTimeEt(self):
        # convert lastCheckTime (UTC) to ET
        raise NotImplementedError

    @hybrid_property
    def totalTestResults(self):
        # Calculated value (positive + negative) of total test results.
        raise NotImplementedError

    # TODO: make a recursive to_dict in the base class to include relationships
    def to_dict(self):
        d = super(CoreData, self).to_dict()
        d['batch'] = self.batch.to_dict()
        return d
