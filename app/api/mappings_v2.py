"""Column mappings defined for API v2. """

import copy


# The leaves are CoreData attributes that should be used to populate these values.
_MAPPING = {
    'cases': {
        'total': 'positive',
        'confirmed': 'positiveCasesViral',
        'probable': 'probableCases',
    },
    'tests': {
        'pcr': {
            'total': 'totalTestResults',
            'pending': 'pending',
            'encounters': {
                'total': 'totalTestEncountersViral',
            },
            'specimens': {
                'total': 'totalTestsViral',
                'positive': 'positiveTestsViral',
                'negative': 'negativeTestsViral',
            },
            'people': {
                'total': 'totalTestsPeopleViral',
                'positive': 'positive',
                'negative': 'negative',
            }
        },
        'antibody': {
            'encounters': {
                'total': 'totalTestsAntibody',
                'positive': 'positiveTestsAntibody',
                'negative': 'negativeTestsAntibody',
            },
            'people': {
                'total': 'totalTestsPeopleAntibody',
                'positive': 'positiveTestsPeopleAntibody',
                'negative': 'negativeTestsPeopleAntibody',
            }
        },
        'antigen': {
            'encounters': {
                'total': 'totalTestsAntigen',
                'positive': 'positiveTestsAntigen',
                'negative': 'negativeTestsAntigen',
            },
            'people': {
                'total': 'totalTestsPeopleAntigen',
                'positive': 'positiveTestsPeopleAntigen',
                'negative': 'negativeTestsPeopleAntigen',
            }
        }
    },
    'outcomes': {
        'recovered': 'recovered',
        'hospitalized': {
            'total': 'hospitalizedCumulative',
            'currently': 'hospitalizedCurrently',
            'in_icu': {
                'total': 'inIcuCumulative',
                'currently': 'inIcuCurrently',
            },
            'on_ventilator': {
                'total': 'onVentilatorCumulative',
                'currently': 'onVentilatorCurrently',
            }
        },
        'death': {
            'total': 'death',
            'confirmed': 'deathConfirmed',
            'probable': 'deathProbable',
        }
    }
}


# Similar to _MAPPING, the leaves are State attributes that should be used to populate these values.
# The only exception is the "label" key/value pairs: these are string literals that will be
# propagated as is to the final output.
_STATE_INFO_MAPPING = {
    'name': 'name',
    'state_code': 'state',
    'fips': 'fips',
    'sites': [
        {
            'url': 'covid19Site',
            'label': 'primary'
        }, {
            'url': 'covid19SiteSecondary',
            'label': 'secondary'
        }, {
            'url': 'covid19SiteTertiary',
            'label': 'tertiary'
        }, {
            'url': 'covid19SiteQuaternary',
            'label': 'quaternary'
        }, {
            'url': 'covid19SiteQuinary',
            'label': 'quinary'
        },
    ],
    'census': {
        'population': 'population',
    },
    'field_sources': {
        'tests': {
            'pcr': {
                'total': 'totalTestResultsField',
            }
        }
    },
    'covid_tracking_project': {
        'preferred_total_test': {
            'field': 'covidTrackingProjectPreferredTotalTestField',
            'units': 'covidTrackingProjectPreferredTotalTestUnits',
        }
    }
}


# US daily data is a small subset of state data. The total test count will be a sum of each state's
# "totalTestResults" entry.
# for each state, since it's going to be handled by that state.

_US_MAPPING = {
    'cases': {
        'total': 'positive',
    },
    'testing': {
        'total': 'totalTestResults',
    },
    'outcomes': {
        'hospitalized': {
            'currently': 'hospitalizedCurrently',
            'in_icu': {
                'currently': 'inIcuCurrently',
            },
            'on_ventilator': {
                'currently': 'onVentilatorCurrently',
            }
        },
        'death': {
            'total': 'death',
        }
    }
}
