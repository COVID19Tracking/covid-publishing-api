import csv
from datetime import datetime, date
from dateutil import parser
import os
import pytz

from app import db
from app.utils.editdiff import EditDiff, ChangedValue, ChangedRow
import logging

from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import class_mapper, relationship, validates


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

    # these fields are only relevant for an edit batch
    changedFields = db.Column(db.String)
    changedDates = db.Column(db.String)
    numRowsEdited = db.Column(db.Integer)

    # false if preview state, true if live
    isPublished = db.Column(db.Boolean, nullable=False)

    # false if part of a regular data push, true if came in through an edit API endpoint
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
    covid19SiteQuaternary = db.Column(db.String)
    covid19SiteQuinary = db.Column(db.String)

    twitter = db.Column(db.String)
    notes = db.Column(db.String)
    pui = db.Column(db.String)
    covidTrackingProjectPreferredTotalTestUnits = db.Column(db.String)
    covidTrackingProjectPreferredTotalTestField = db.Column(db.String)
    totalTestResultsField = db.Column(db.String)
    totalTestResultsFieldDbColumn = db.Column(db.String, nullable=False)

    # here for parity with public API, deprecated field
    @hybrid_property
    def pum(self):
        return False

    @hybrid_property
    def fips(self):
        return fips_lookup(self.state)

    @validates('totalTestResultsFieldDbColumn')
    def validate_totalTestResultsFieldDbColumn(self, key, value):
        """Validate the totalTestResultsFieldDbColumn value, used to calculate totalTestResults.

        Acceptable values are either a valid CoreData column name or a known special keyword like 'posNeg'.
        """
        ttr_special_keywords = ['posNeg']
        is_valid = value in ttr_special_keywords or value in [column.name for column in CoreData.__table__.columns]
        assert is_valid, "invalid value for totalTestResultsFieldDbColumn"
        return value

    def __init__(self, **kwargs):
        mapper = class_mapper(State)
        relevant_kwargs = {k: v for k, v in kwargs.items() if k in mapper.attrs.keys()}
        super(State, self).__init__(**relevant_kwargs)


class CoreData(db.Model, DataMixin):
    __tablename__ = 'coreData'

    # composite PK: state_name, batch_id, date
    state = db.Column(db.String, db.ForeignKey('states.state'),
        nullable=False, primary_key=True)
    state_obj = relationship("State", lazy="selectin")

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
    def totalTestResultsSource(self):
        """The source column used to calculate totalTestResults, equal to the state's totalTestResultsFieldDbColumn"""
        return self.state_obj.totalTestResultsFieldDbColumn

    @hybrid_property
    def totalTestResults(self):
        """Calculated value of total test results

        This value is determined based on the state's totalTestResultsFieldDbColumn, with empty cells converted to 0.
        If a CoreData column name is specified, that column will be used for totalTestResults.
        Alternatively, the 'posNeg' keyword can be used to indicate totalTestResults = (positive+negative)"""
        column = self.totalTestResultsSource

        if column == 'posNeg':  # posNeg: calculated value (positive + negative) of total test results.
            if self.negative is None:
                return self.positive or 0
            if self.positive is None:
                return self.negative or 0
            return self.positive + self.negative
        else:  # column is a coreData column, return its value, converting none to 0
            value = getattr(self, column)
            return value

    # Converts the input to a string and returns parsed datetime.date object
    @staticmethod
    def parse_str_to_date(date_input):
        return parser.parse(str(date_input), ignoretz=True).date()

    @staticmethod
    def valid_fields_checker(candidates):
        '''
        dict[string] -> ([string], [string])
        Gets a list of field names and returns a tuple of (valid_fields, unknown_fields).

        If valid_fields is empty, then this list contains no data for this object.
        If unknown_fields is not-empty, then this list contains extra fields
        that mean nothing for this object, but we might want to alert on this.
        In the valid fields, we exclude state, date and batchId because these are the
        primary keys for the record, and all keys without values make it a dull record
        '''
        mapper = class_mapper(CoreData)
        keys = mapper.attrs.keys()

        candidate_set = set(candidates)
        key_set = set(keys)
        unknowns = candidate_set - key_set
        valid = candidate_set & key_set
        valid = valid - {x.name for x in mapper.primary_key}
        return (valid, unknowns)

    def field_diffs(self, dict_other):
        ''' Return the list of fields that dict_other would modify if applied
        on this row.
        Some business logic is applied, and some fields are skipped from comparison, field
        aliases get special treatment.

        Return ChangedRow if there are changes, or None if no changes
        '''
        diffs = []
        if not dict_other:
            return None

        # we want to compare after all parsing is done
        other = CoreData(**dict_other)

        # special casing for date aliases
        # TODO: define the ordering of expected date fields, and expectations
        # if multiple aliases for the same field exist
        if 'lastUpdateIsoUtc' in dict_other and not 'lastUpdateTime' in dict_other:
            # if both fields exist this is not ideal, but the object prefers 'lastUpdateTime'.
            # for now, 'lastUpdateTime' wins
            dict_other['lastUpdateTime'] = dict_other['lastUpdateIsoUtc']

        for field in CoreData.__table__.columns.keys():
            # we expect batch IDs to be different, skip comparing those
            if field == 'batchId':
                continue
            # for any other field, compare away
            if field in dict_other and getattr(other, field) != getattr(self, field):
                old = getattr(self, field)
                new = getattr(other, field)
                diffs.append(ChangedValue(field=field, old=old, new=new))

        if diffs:
            changes = ChangedRow(date=self.date, state=self.state, changed_values=diffs)
            return changes
        return None

    @staticmethod
    def _cleanup_date_kwargs(kwargs):
        # accept either lastUpdateTime or lastUpdateIsoUtc as an input
        last_update_time = kwargs.get('lastUpdateTime') or kwargs.get('lastUpdateIsoUtc')
        if last_update_time:
            if isinstance(last_update_time, str):
                last_update_time = parser.parse(last_update_time)
            if last_update_time.tzinfo is None:
                raise ValueError(
                    'Expected a timezone with last update time: %s' % last_update_time)
            kwargs['lastUpdateTime'] = last_update_time

        date_checked = kwargs.get('dateChecked')
        if date_checked:
            if isinstance(date_checked, str):
                date_checked = parser.parse(date_checked)
            if date_checked.tzinfo is None:
                raise ValueError(
                    'Expected a timezone with dateChecked: %s' % kwargs['dateChecked'])
            kwargs['dateChecked'] = date_checked

        # "date" is expected to be a date string, no times or timezones
        if 'date' in kwargs:
            kwargs['date'] = CoreData.parse_str_to_date(kwargs['date'])
        else:
            kwargs['date'] = date.today()
        return kwargs

    def copy_with_updates(self, **kwargs):
        kwargs = self._cleanup_date_kwargs(kwargs)
        self_props = self.to_dict()
        self_props.update(kwargs)
        return CoreData(**self_props)

    def __init__(self, **kwargs):
        # strip any empty string fields from kwargs
        kwargs = {k: v for k, v in kwargs.items() if v is not None and v != ""}
        kwargs = self._cleanup_date_kwargs(kwargs)

        mapper = class_mapper(CoreData)
        relevant_kwargs = {k: v for k, v in kwargs.items() if k in mapper.attrs.keys()}
        super(CoreData, self).__init__(**relevant_kwargs)
