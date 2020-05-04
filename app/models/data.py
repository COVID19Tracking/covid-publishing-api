"""This is an example model which will be used for creating stories on the web.
The model is defined in a similar way to python class/object, however is
inherited from a SQLAlchemy class so a DB entry with a table can be built
easily
"""

from datetime import datetime
from app import db


class Batch(db.Model):
    __tablename__ = 'batch'

    # primary key
    batch_id = db.Column(db.Integer, primary_key=True)

    created_at = db.Column()
    published_at = db.Column()
    shift_lead = db.Column()
    batch_note = db.Column()
    data_entry_type = db.Column()
    is_published = db.Column()
    is_revision = db.Column()    

    def __init__(self, **kwargs):
        super(Batch, self).__init__(**kwargs)

    def to_dict(self):
        d = {}
        for column in self.__table__.columns:
            d[column.name] = str(getattr(self, column.name))
        return d
