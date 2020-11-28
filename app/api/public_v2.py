"""Registers the necessary routes for the public API v2 endpoints."""

from collections import defaultdict
import copy
from datetime import timedelta
from itertools import filterfalse

import flask
from flask import json, request
from flask_restful import inputs
from time import perf_counter

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
    },
    'data_quality_grade': 'dataQualityGrade'
}

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


def get_value(core_data, field_name):
    if isinstance(core_data, CoreData):
        return getattr(core_data, field_name)
    elif isinstance(core_data, dict):
        return core_data.get(field_name)
    else:
        raise ValueError("Unexpected input type: %s" % type(core_data))


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
            state = get_value(data_for_day, 'state') or 'US'   # state is 'US' if national
            self.key_to_date[state][get_value(data_for_day, 'date')] = data_for_day

        # omit computing derived values for the following non-numeric and other fields
        self.do_not_calculate_fields = [
            'dataQualityGrade',
            'hospitalizedCumulative',
            'inIcuCumulative',
            'onVentilatorCumulative']

    @staticmethod
    def get_date(core_data):
        date = get_value(core_data, 'date')
        if isinstance(date, str):
            date = CoreData.parse_str_to_date(date)
        return date

    def population_percent(self, core_data, field_name):
        field_value_for_day = get_value(core_data, field_name)
        if field_value_for_day is None:
            return None

        state = get_value(core_data, 'state') or 'US'
        # call population_lookup directly instead of using the state property to support lookup for 'US':
        state_population = population_lookup(state)
        pop_pct = field_value_for_day / state_population
        return round(pop_pct * 100, 4)

    def change_from_prior_day(self, core_data, field_name):
        field_value_for_day = get_value(core_data, field_name)
        if field_value_for_day is None:
            return None

        prior_day = ValuesCalculator.get_date(core_data) - timedelta(days=1)
        # compute change_from_prior_day, if it exists
        state = get_value(core_data, 'state') or 'US'
        if prior_day in self.key_to_date[state]:
            data_for_prior_day = self.key_to_date[state][prior_day]
            field_value_for_prior_day = get_value(data_for_prior_day, field_name)
            if field_value_for_day is not None and field_value_for_prior_day is not None:
                return field_value_for_day - field_value_for_prior_day

        return None

    def seven_day_change_percent(self, core_data, field_name):
        field_value_for_day = get_value(core_data, field_name)
        if field_value_for_day is None:
            return None

        week_ago_day = ValuesCalculator.get_date(core_data) - timedelta(days=7)
        state = get_value(core_data, 'state') or 'US'
        if week_ago_day in self.key_to_date[state]:
            data_for_week_ago = self.key_to_date[state][week_ago_day]
            field_value_for_week_ago = get_value(data_for_week_ago, field_name)
            if field_value_for_day is not None and \
                    field_value_for_week_ago is not None and \
                    field_value_for_week_ago > 0:
                pct_change = (field_value_for_day-field_value_for_week_ago)/field_value_for_week_ago
                return round(pct_change * 100, 1)

        return None

    def seven_day_average(self, core_data, field_name):
        field_value_for_day = get_value(core_data, field_name)
        if field_value_for_day is None:
            return None

        state = get_value(core_data, 'state') or 'US'
        seven_day_values = []
        for i in range(7):
            some_prior_date = ValuesCalculator.get_date(core_data) - timedelta(days=i)
            if some_prior_date in self.key_to_date[state]:
                data_for_some_prior_date = self.key_to_date[state][some_prior_date]
                field_value_for_some_prior_date = get_value(data_for_some_prior_date, field_name)
                if field_value_for_some_prior_date is not None:
                    seven_day_values.append(field_value_for_some_prior_date)

        assert len(seven_day_values) <= 7
        if len(seven_day_values) > 0:
            return round(sum(seven_day_values) / len(seven_day_values))

        return None

    def calculate_values(self, core_data, field_name):
        """
        Returns calculated values for the given core data field as a dictionary. If the field name
        is in the list of fields to not calculate, returns None.

        Parameters
        ----------
        core_data : CoreData
            The CoreData object for which we need to calculate a bunch of derived values 
        field_name : str
            The CoreData property we're calculating values for, e.g. "positiveTestsViral"
        """
        if field_name in self.do_not_calculate_fields:
            return None

        return {
            'population_percent': self.population_percent(core_data, field_name),
            'change_from_prior_day': self.change_from_prior_day(core_data, field_name),
            'seven_day_average': self.seven_day_average(core_data, field_name),
            'seven_day_change_percent': self.seven_day_change_percent(core_data, field_name),
        }


def recursive_tree_to_output(tree, core_data, calculator=None):
    # walk through the data tree recursively and populate the fields from core_data
    if isinstance(tree, list):
        for v in tree:
            recursive_tree_to_output(v, core_data, calculator)
            return

    # tree is a dict
    for k, v in tree.items():
        # if k is 'label', it's a string literal field and should be left unchanged
        if k is 'label':
            tree[k] = v
        # if v is a string, we're at a leaf, need to replace v with the actual value from core_data
        elif isinstance(v, str):
            value = getattr(core_data, v)
            if calculator:  # need to compute values for the "full" output
                leaf_dict = {'value': value}
                calculated_values = calculator.calculate_values(core_data, v)
                if calculated_values is not None:
                    leaf_dict['calculated'] = calculated_values
                tree[k] = leaf_dict
            else:
                tree[k] = value
        else:
            # need to recurse one level down
            recursive_tree_to_output(v, core_data, calculator)


def convert_core_data_to_simple_output(core_data):
    core_data_copy = copy.deepcopy(_MAPPING)
    recursive_tree_to_output(core_data_copy, core_data)
    return core_data_copy


def convert_core_data_to_full_output(core_data, calculator):
    core_data_copy = copy.deepcopy(_MAPPING)
    recursive_tree_to_output(core_data_copy, core_data, calculator)
    return core_data_copy


def convert_state_info_to_output(state_data):
    state_data_copy = copy.deepcopy(_STATE_INFO_MAPPING)
    recursive_tree_to_output(state_data_copy, state_data)

    # remove all sites that do not have a url defined
    state_data_copy['sites'][:] = filterfalse(lambda site: site['url'] is None, state_data_copy['sites'])

    return state_data_copy


def output_with_metadata(data, link):
    out = {'links': {'self': link},
           'meta': {
               'build_time': datetime.utcnow().isoformat()[:-3] + 'Z',
               'license': 'CC-BY-4.0',
               'version': '2.0-beta',
           },
           'data': data,
    }
    return out


# FOR LATER: this is hard because us_daily_query doesn't return CoreData objects, but instead
# it returns dicts. So we need to change the approach here.
def get_us_daily_v2_internal(include_preview=False, simple=False):
    latest_daily_data = us_daily_query(preview=include_preview)
    out = {}

    link = 'https://api.covidtracking.com/us/daily'
    if simple:
        link += '/simple'
    out['links'] = {'self': link}
    out['meta'] = {
        'build_time': '2020-11-11T21:54:35.153Z',  # TODO: fix this placeholder
        'license': 'CC-BY-4.0',
        'version': '2.0-beta',
    }
    out['data'] = []

    # only do the caching/precomputation of calculated data if we need to
    calculator = None
    if not simple:
        calculator = ValuesCalculator(latest_daily_data)

    for core_data in latest_daily_data:
        # sometimes we have empty rows that only have date and state set but no actual data
        if len(core_data) == 0:
            continue

        core_data_nested_dict = {
            'date': get_value(core_data, 'date'),
            'states': get_value(core_data, 'states'),
        }

        if simple:
            core_actual_data_dict = convert_core_data_to_simple_output(core_data)
        else:
            core_actual_data_dict = convert_core_data_to_full_output(core_data, calculator)

        # remove data_quality_grade from the output, it only means something for states
        core_actual_data_dict.pop('data_quality_grade')

        core_data_nested_dict.update(core_actual_data_dict)
        out['data'].append(core_data_nested_dict)

    response = flask.current_app.response_class(
        json.dumps(out, sort_keys=False, indent=2),
        mimetype=flask.current_app.config['JSONIFY_MIMETYPE'])
    return response


def get_states_daily_v2_internal(state=None, include_preview=False, simple=False):
    latest_daily_data = states_daily_query(
        state=state.upper() if state else None, preview=include_preview).all()
    if len(latest_daily_data) == 0:
        # likely state not found
        return flask.Response(
            'States Daily data unavailable for state %s' % state if state else 'all')

    base_link = 'https://api.covidtracking.com/states'
    link = '%s/%s/daily' % (base_link, state) if state else '%s/daily' % (base_link)
    if simple:
        link += '/simple'

    # only do the caching/precomputation of calculated data if we need to
    calculator = None
    if not simple:
        calculator = ValuesCalculator(latest_daily_data)

    out_data = []
    for core_data in latest_daily_data:
        meta = {
            'updated': '2020-11-08T23:59:00.000-08:00',  # TODO: where should this come from?
            'tests': {  # TODO: should there be any other fields besides tests source?
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
        out_data.append(core_data_nested_dict)

    out = output_with_metadata(out_data, link)
    response = flask.current_app.response_class(
        json.dumps(out, sort_keys=False, indent=2),
        mimetype=flask.current_app.config['JSONIFY_MIMETYPE'])
    return response


@api.route('/v2/public/states/<string:state>/daily/simple', methods=['GET'])
@api.route('/v2/public/states/daily/simple', methods=['GET'])
def get_states_daily_simple_v2(state=None):
    t1 = perf_counter()
    flask.current_app.logger.info(
        'Retrieving simple States Daily v2 for state %s' % (state if state else 'all'))
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    resp = get_states_daily_v2_internal(state=state, include_preview=include_preview, simple=True)
    t2 = perf_counter()
    flask.current_app.logger.info(
        'Simple States Daily v2 for state %s took %.1f sec' % (state if state else 'all', t2 - t1))
    return resp


@api.route('/v2/public/states/<string:state>/daily', methods=['GET'])
@api.route('/v2/public/states/daily', methods=['GET'])
def get_states_daily_v2(state=None):
    t1 = perf_counter()
    flask.current_app.logger.info(
        'Retrieving States Daily v2 for state %s' % (state if state else 'all'))
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    resp = get_states_daily_v2_internal(state=state, include_preview=include_preview, simple=False)
    t2 = perf_counter()
    flask.current_app.logger.info(
        'States Daily v2 for state %s took %.1f sec' % (state if state else 'all', t2 - t1))
    return resp


@api.route('/v2/public/states', methods=['GET'])
def get_state_v2():
    states = State.query.order_by(State.state.asc()).all()
    out_data = []
    for state in states:
        out_data.append(convert_state_info_to_output(state))

    link = 'https://api.covidtracking.com/states'
    out_data = output_with_metadata(out_data, link)

    return flask.current_app.response_class(
        json.dumps(out_data, sort_keys=False, indent=2),
        mimetype=flask.current_app.config['JSONIFY_MIMETYPE'])


@api.route('/v2/public/us/daily/simple', methods=['GET'])
def get_us_daily_simple_v2():
    t1 = perf_counter()
    flask.current_app.logger.info('Retrieving simple US Daily v2')
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    resp = get_us_daily_v2_internal(include_preview=include_preview, simple=True)
    t2 = perf_counter()
    flask.current_app.logger.info('Simple US Daily v2 took %.1f sec' % (t2 - t1))
    return resp


@api.route('/v2/public/us/daily', methods=['GET'])
def get_us_daily_v2():
    t1 = perf_counter()
    flask.current_app.logger.info('Retrieving US Daily v2')
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    resp = get_us_daily_v2_internal(include_preview=include_preview, simple=False)
    t2 = perf_counter()
    flask.current_app.logger.info('US Daily v2 took %.1f sec' % (t2 - t1))
    return resp
