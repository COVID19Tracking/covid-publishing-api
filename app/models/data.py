"""This is an example model which will be used for creating stories on the web.
The model is defined in a similar way to python class/object, however is
inherited from a SQLAlchemy class so a DB entry with a table can be built
easily
"""

from datetime import datetime
from app import db

from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import relationship

class DataMixin(object):

    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    def to_dict(self):
        d = {}
        for column in self.__table__.columns:
            d[column.name] = str(getattr(self, column.name))
        return d


class Batch(db.Model, DataMixin):
    __tablename__ = 'batch'

    # primary key
    batch_id = db.Column(db.Integer, primary_key=True)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    published_at = db.Column(db.DateTime(timezone=True))
    shift_lead = db.Column(db.String(100))
    batch_note = db.Column(db.String)
    data_entry_type = db.Column(db.String)

    # false if preview state, true if live
    is_published = db.Column(db.Boolean, nullable=False)
    is_revision = db.Column(db.Boolean, nullable=False)

    core_data_rows = relationship('CoreData', backref='batch')

    def __init__(self, **kwargs):
        super(Batch, self).__init__(**kwargs)


class State(db.Model, DataMixin):
    __tablename__ = 'states'

    state_name = db.Column(db.String, primary_key=True, nullable=False)
    full_name = db.Column(db.String)

    core_data_rows = relationship('CoreData', backref='state')

    def __init__(self, **kwargs):
        super(State, self).__init__(**kwargs)


class CoreData(db.Model, DataMixin):
    __tablename__ = 'core_data'

    last_update_time = db.Column(db.DateTime(timezone=True), nullable=False)
    last_check_time = db.Column(db.DateTime(timezone=True), nullable=False)

    # the day we mean to report this data for; meant for "states daily" extraction
    data_date = db.Column(db.Date, nullable=False)

    tests = db.Column(db.Integer)
    # TODO: additional cols to follow for positives, negatives, hospitalization data, etc.

    checker = db.Column(db.String(100))
    double_checker = db.Column(db.String(100))
    public_notes = db.Column(db.String)

    # from worksheet, "Notes" column (made by checker or doublechecker)
    private_notes = db.Column(db.String)

    # from state matrix: which columns?
    source_notes = db.Column(db.String)

    # composite PK: state_name, batch_id
    state_name = db.Column(db.String, db.ForeignKey('states.state_name'), 
        nullable=False, primary_key=True)
    batch_id = db.Column(db.Integer, db.ForeignKey('batch.batch_id'),
        nullable=False, primary_key=True)

    def __init__(self, **kwargs):
        super(CoreData, self).__init__(**kwargs)

    # TODO: make a recursive to_dict in the base class to include relationships
    def to_dict(self):
        d = super(CoreData, self).to_dict()
        d['batch'] = self.batch.to_dict()
        d['state'] = self.state.to_dict()
        return d
