# This is strictly data, but JSON has no comments
# and YAML requires additional dependencies

''' Mapping from DB column name to CSV display name
'''

import collections

from sqlalchemy.sql import literal_column, func
from enum import Enum
from app.models.data import Batch, CoreData, State


CSVColumn = collections.namedtuple('Column', 'label model_column blank')
# set default value of the blank parameter to false, all other params are required
CSVColumn.__new__.__defaults__ = (False, )

class Literal:
    def __init__(self, name):
        self.name = name

COLUMNS_DISPLAY_NAMES = {
    # TODO: replace strings with column keys

    "date": "Date",
    "state": "State",
    "states": "States",
    "positive": "Positive",
    "negative": "Negative",
    "pending": "Pending",
    "hospitalizedCurrently": "Hospitalized – Currently",
    "hospitalizedCumulative": "Hospitalized – Cumulative",
    "inIcuCurrently": "In ICU – Currently",
    "inIcuCumulative": "In ICU – Cumulative",
    "onVentilatorCurrently": "On Ventilator – Currently",
    "onVentilatorCumulative": "On Ventilator – Cumulative",
    "recovered": "Recovered",
    "death": "Deaths",
    "dataQualityGrade": "Data Quality Grade",
    "lastUpdateEt": "Last Update ET",
    "totalTestsAntibody": "Total Antibody Tests",
    "positiveTestsAntibody": "Positive Antibody Tests",
    "negativeTestsAntibody": "Negative Antibody Tests",
    "totalTestsViral": "Total Tests (PCR)",
    "positiveTestsViral": "Positive Tests (PCR)",
    "negativeTestsViral": "Negative Tests (PCR)",
    "positiveCasesViral": "Positive Cases (PCR)",
    "deathConfirmed": "Deaths (confirmed)",
    "deathProbable": "Deaths (probable)",
    "totalTestsPeopleViral": "Total PCR Tests (People)",
    "probableCases": "Probable Cases",
    "totalTestEncountersViral": "Total Test Encounters (PCR)",
    "totalTestsPeopleAntibody": "Total Antibody Tests (People)",
    "positiveTestsPeopleAntibody": "Positive Antibody Tests (People)",
    "negativeTestsPeopleAntibody": "Negative Antibody Tests (People)",
    "totalTestsPeopleAntigen": "Total Antigen Tests (People)",
    "positiveTestsPeopleAntigen": "Positive Antigen Tests (People)",
    "negativeTestsPeopleAntigen": "Negative Antigen Tests (People)",
    "totalTestsAntigen": "Total Antigen Tests",
    "positiveTestsAntigen": "Positive Antigen Tests",
    "negativeTestsAntigen": "Negative Antigen Tests",
    "totalTestResults": "Total Test Results",
}


US_CURRENT_COLUMNS = [
    CoreData.positive,
    CoreData.negative,
    CoreData.pending,
    CoreData.hospitalizedCurrently,
    CoreData.hospitalizedCumulative,
    CoreData.inIcuCurrently,
    CoreData.inIcuCumulative,
    CoreData.onVentilatorCurrently,
    CoreData.onVentilatorCumulative,
    CoreData.recovered,
    CoreData.death,
]


US_DAILY_COLUMNS = [CoreData.date, Literal("states")] + US_CURRENT_COLUMNS



STATES_CURRENT = [
    CoreData.state,
    CoreData.positive,
    CoreData.negative,
    CoreData.pending,
    CoreData.hospitalizedCurrently,
    CoreData.hospitalizedCumulative,
    CoreData.inIcuCurrently,
    CoreData.inIcuCumulative,
    CoreData.onVentilatorCurrently,
    CoreData.onVentilatorCumulative,
    CoreData.recovered,
    CoreData.death,


    Literal("lastUpdateEt"),
    #CoreData.lastUpdateEt,
    CoreData.dateChecked
]

STATES_DAILY = [
    #func.to_char(CoreData.date, 'YYYYMMDD').label('date'),
    CoreData.date,
    CoreData.state,
    CoreData.positive,
    CoreData.negative,
    CoreData.pending,
    CoreData.hospitalizedCurrently,
    CoreData.hospitalizedCumulative,
    CoreData.inIcuCurrently,
    CoreData.inIcuCumulative,
    CoreData.onVentilatorCurrently,
    CoreData.onVentilatorCumulative,
    CoreData.recovered,
    CoreData.death,

    CoreData.dataQualityGrade,
    #CoreData.lastUpdateEt,
    Literal("lastUpdateEt"),
    CoreData.totalTestsAntibody,
    CoreData.positiveTestsAntibody,
    CoreData.negativeTestsAntibody,
    CoreData.totalTestsViral,
    CoreData.positiveTestsViral,
    CoreData.negativeTestsViral,
    CoreData.positiveCasesViral,
    CoreData.deathConfirmed,
    CoreData.deathProbable,
    CoreData.probableCases,
    CoreData.totalTestEncountersViral,
    CoreData.totalTestsPeopleAntibody,
    CoreData.positiveTestsPeopleAntibody,
    CoreData.negativeTestsPeopleAntibody,
    CoreData.totalTestsPeopleAntigen,
    CoreData.positiveTestsPeopleAntigen,
    CoreData.negativeTestsPeopleAntigen,
    CoreData.totalTestsAntigen,
    CoreData.positiveTestsAntigen,
    CoreData.negativeTestsAntigen,

    # Fake Column
    literal_column("''").label('_posNeg'),

    #CoreData.totalTestResults
    Literal("totalTestResults"),
]


def select(columns):
    return [CSVColumn(
        label=COLUMNS_DISPLAY_NAMES.get(c.name) if c.name in COLUMNS_DISPLAY_NAMES else c.name,
        model_column=c.name if c.name in COLUMNS_DISPLAY_NAMES else None,
        blank=c in COLUMNS_DISPLAY_NAMES)
            for c in columns]
