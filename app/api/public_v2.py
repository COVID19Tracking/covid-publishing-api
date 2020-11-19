"""Registers the necessary routes for the public API v2 endpoints."""

from collections import defaultdict
import copy
from datetime import timedelta
import flask
from flask import json, request
from flask_restful import inputs

from app.api import api
from app.api.common import states_daily_query, us_daily_query
from app.models.data import *


# The leaves are CoreData attributes that should be used to populate these values.
_MAPPING = {
    'cases': {
        'total': 'positive',
        'confirmed': 'positiveCasesViral',
        'probable': 'probableCases',
    },
    'tests': {
        'pcr': {
            'total': 'totalTestsViral',
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


class ValuesCalculator(object):
    def __init__(self, daily_data):
        """
        Parameters
        ----------
        daily_data : list(CoreData)
            The full States or US Daily result, used for deriving values relating to data from the
            day or week before.
        """
        # break down the daily data by state/date for faster lookups: state -> date -> data
        self.key_to_date = defaultdict(dict)
        for data_for_day in daily_data:
            state = getattr(data_for_day, 'state') or 'US'   # state is 'US' if national
            self.key_to_date[state][data_for_day.date] = data_for_day

    def change_from_prior_day(self, core_data, field_name):
        field_value_for_day = getattr(core_data, field_name)
        if field_value_for_day is None:
            return None

        prior_day = core_data.date - timedelta(days=1)
        # compute change_from_prior_day, if it exists
        state = getattr(core_data, 'state') or 'US'
        if prior_day in self.key_to_date[state]:
            data_for_prior_day = self.key_to_date[state][prior_day]
            field_value_for_prior_day = getattr(data_for_prior_day, field_name)
            if field_value_for_day is not None and field_value_for_prior_day is not None:
                return field_value_for_day - field_value_for_prior_day

        return None

    def seven_day_change_percent(self, core_data, field_name):
        field_value_for_day = getattr(core_data, field_name)
        if field_value_for_day is None:
            return None

        week_ago_day = core_data.date - timedelta(days=7)
        state = getattr(core_data, 'state') or 'US'
        if week_ago_day in self.key_to_date[state]:
            data_for_week_ago = self.key_to_date[state][week_ago_day]
            field_value_for_week_ago = getattr(data_for_week_ago, field_name)
            if field_value_for_day is not None and \
                    field_value_for_week_ago is not None and \
                    field_value_for_week_ago > 0:
                pct_change = (field_value_for_day-field_value_for_week_ago)/field_value_for_week_ago
                return round(pct_change * 100, 1)

        return None

    def seven_day_average(self, core_data, field_name):
        field_value_for_day = getattr(core_data, field_name)
        if field_value_for_day is None:
            return None

        state = getattr(core_data, 'state') or 'US'
        seven_day_values = []
        for i in range(7):
            some_prior_date = core_data.date - timedelta(days=i)
            if some_prior_date in self.key_to_date[state]:
                data_for_some_prior_date = self.key_to_date[state][some_prior_date]
                field_value_for_some_prior_date = getattr(data_for_some_prior_date, field_name)
                if field_value_for_some_prior_date is not None:
                    seven_day_values.append(field_value_for_some_prior_date)

        assert len(seven_day_values) <= 7
        if len(seven_day_values) > 0:
            return sum(seven_day_values) / len(seven_day_values)

        return None

    def calculate_values(self, core_data, field_name):
        """
        Returns calculated values for the given core data field as a dictionary.

        Parameters
        ----------
        core_data : CoreData
            The CoreData object for which we need to calculate a bunch of derived values 
        field_name : str
            The CoreData property we're calculating values for, e.g. "positiveTestsViral"
        """
        return {
            'population_percent': None,  # TODO: compute this
            'change_from_prior_day': self.change_from_prior_day(core_data, field_name),
            'seven_day_average': self.seven_day_average(core_data, field_name),
            'seven_day_change_percent': self.seven_day_change_percent(core_data, field_name),
        }


def recursive_tree_to_simple_output(tree, core_data):
    # walk through it recursively and populate the fields from core_data
    for k, v in tree.items():
        # if v is a string, we're at a leaf, need to replace v with the actual value from core_data
        if isinstance(v, str):
            tree[k] = getattr(core_data, v)
        else:
            # need to recurse one level down
            recursive_tree_to_simple_output(v, core_data)


def convert_core_data_to_simple_output(core_data):
    core_data_copy = copy.deepcopy(_MAPPING)
    recursive_tree_to_simple_output(core_data_copy, core_data)
    return core_data_copy


def recursive_tree_to_full_output(tree, core_data, calculator):
    # walk through it recursively and populate the fields from core_data
    for k, v in tree.items():
        # if v is a string, we're at a leaf and v is the field name we need to use. need to replace
        # v with the actual value from core_data as well as the derived values we've computed
        if isinstance(v, str):
            value = getattr(core_data, v)
            # flask.current_app.logger.info(f'Calculating values for {k} where {v} is leaf')
            calculated_values = calculator.calculate_values(core_data, v)
            output = {
                'value': value,
                'calculated': calculated_values,
            }
            tree[k] = output
        else:
            # need to recurse one level down
            recursive_tree_to_full_output(v, core_data, calculator)


def convert_core_data_to_full_output(core_data, calculator):
    core_data_copy = copy.deepcopy(_MAPPING)
    recursive_tree_to_full_output(core_data_copy, core_data, calculator)
    return core_data_copy


def get_states_daily_v2_internal(state=None, include_preview=False, simple=False):
    latest_daily_data = states_daily_query(
        state=state.upper() if state else None, preview=include_preview).all()
    if len(latest_daily_data) == 0:
        # likely state not found
        return flask.Response(
            'States Daily data unavailable for state %s' % state if state else 'all')

    out = {}

    base_link = 'https://api.covidtracking.com/v2/states'
    link = '%s/%s/daily' % (base_link, state) if state else '%s/daily' % (base_link)
    if simple:
        link += '/simple'
    out['links'] = {'self': link}
    out['meta'] = {
        'build_time': '2020-11-11T21:54:35.153Z',
        'license': 'CC-BY-4.0',
        'version': '2.0-beta',
    }
    out['data'] = []

    # only do the caching/precomputation of calculated data if we need to
    calculator = None
    if not simple:
        calculator = ValuesCalculator(latest_daily_data)

    for core_data in latest_daily_data:
        meta = {
            'data_quality_grade': 'PLACEHOLDER',  # TODO: move this into "data" out of "metadata"
            'updated': '2020-11-08T23:59:00.000-08:00',  # TODO: where should this come from?
            'tests': {   # TODO: should there be any other fields besides tests source?
                'total_source': core_data.totalTestResultsSource
            }
        }
        core_data_nested_dict = {
            'date': core_data.date.strftime('%Y-%m-%d'),
            'state': core_data.state,
            'meta': meta,
        }

        if simple:
            core_actual_data_dict = convert_core_data_to_simple_output(core_data)
        else:
            core_actual_data_dict = convert_core_data_to_full_output(core_data, calculator)

        core_data_nested_dict.update(core_actual_data_dict)
        out['data'].append(core_data_nested_dict)

    response = flask.current_app.response_class(
        json.dumps(out, sort_keys=False, indent=2),
        mimetype=flask.current_app.config['JSONIFY_MIMETYPE'])
    return response


@api.route('/v2/public/states/<string:state>/daily/simple', methods=['GET'])
@api.route('/v2/public/states/daily/simple', methods=['GET'])
def get_states_daily_simple_v2(state=None):
    flask.current_app.logger.info(
        'Retrieving simple States Daily v2 for state %s' % (state if state else 'all'))
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    return get_states_daily_v2_internal(state=state, include_preview=include_preview, simple=True)


@api.route('/v2/public/states/<string:state>/daily', methods=['GET'])
@api.route('/v2/public/states/daily', methods=['GET'])
def get_states_daily_v2(state=None):
    flask.current_app.logger.info(
        'Retrieving States Daily v2 for state %s' % (state if state else 'all'))
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    return get_states_daily_v2_internal(state=state, include_preview=include_preview, simple=False)
