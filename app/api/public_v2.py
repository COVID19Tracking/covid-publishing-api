"""Registers the necessary routes for the public API v2 endpoints."""

from collections import OrderedDict
import flask
from flask import json, request
from flask_restful import inputs

from app.api import api
from app.api.common import states_daily_query, us_daily_query
from app.models.data import *


def states_daily_simple_from_core_data(core_data):
    out = {
        'cases': {
            'total': core_data.positive,
            'confirmed': core_data.positiveCasesViral,
            'probable': core_data.probableCases,
        },
        'tests': {
            'pcr': {
                'total': core_data.totalTestsViral,
                'pending': core_data.pending,
                'encounters': {
                    'total': core_data.totalTestEncountersViral,
                },
                'specimens': {
                    'total': core_data.totalTestsViral,
                    'positive': core_data.positiveTestsViral,
                    'negative': core_data.negativeTestsViral,
                },
                'people': {
                    'total': core_data.totalTestsPeopleViral,
                    'positive': core_data.positive,
                    'negative': core_data.negative,
                }
            },
            'antibody': {
                'encounters': {
                    'total': core_data.totalTestsAntibody,
                    'positive': core_data.positiveTestsAntibody,
                    'negative': core_data.negativeTestsAntibody,
                },
                'people': {
                    'total': core_data.totalTestsPeopleAntibody,
                    'positive': core_data.positiveTestsPeopleAntibody,
                    'negative': core_data.negativeTestsPeopleAntibody,
                }
            },
            'antigen': {
                'encounters': {
                    'total': core_data.totalTestsAntigen,
                    'positive': core_data.positiveTestsAntigen,
                    'negative': core_data.negativeTestsAntigen,
                },
                'people': {
                    'total': core_data.totalTestsPeopleAntigen,
                    'positive': core_data.positiveTestsPeopleAntigen,
                    'negative': core_data.negativeTestsPeopleAntigen,
                }
            }
        },
        'outcomes': {
            'recovered': core_data.recovered,
            'hospitalized': {
                'total': core_data.hospitalizedCumulative,
                'currently': core_data.hospitalizedCurrently,
                'in_icu': {
                    'total': core_data.inIcuCumulative,
                    'currently': core_data.inIcuCurrently,
                },
                'on_ventilator': {
                    'total': core_data.onVentilatorCumulative,
                    'currently': core_data.onVentilatorCurrently,
                }
            },
            'death': {
                'total': core_data.death,
                'confirmed': core_data.deathConfirmed,
                'probable': core_data.deathProbable,
            }
        }
    }

    return out


@api.route('/v2/public/states/<string:state>/daily/simple', methods=['GET'])
@api.route('/v2/public/states/daily/simple', methods=['GET'])
def get_states_daily_simple_for_state_v2(state=None):
    flask.current_app.logger.info(
        'Retrieving simple States Daily v2 for state %s' % (state if state else 'all'))
    include_preview = request.args.get('preview', default=False, type=inputs.boolean)
    latest_daily_data = states_daily_query(
        state=state.upper() if state else None, preview=include_preview).all()
    if len(latest_daily_data) == 0:
        # likely state not found
        return flask.Response(
            "States Daily data unavailable for state %s" % state if state else 'all', status=404)

    out = {}
    out['links'] = {'self': 'https://api.covidtracking.com/v2/states/%s/daily/simple' % state}
    out['meta'] = {
        'build_time': '2020-11-11T21:54:35.153Z',
        'license': 'CC-BY-4.0',
        'version': '2.0-beta',
    }
    out['data'] = []

    for core_data in latest_daily_data:
        meta = {
            # TODO: is data_quality_grade the only meta field here?
            "data_quality_grade": "PLACEHOLDER",  # TODO: get data quality grades in here
            "updated": "2020-11-08T23:59:00.000-08:00",  # TODO: where should this come from?
            "tests": {   # TODO: should there be any other fields besides tests source?
                "total_source": core_data.totalTestResultsSource
            }
        }
        core_data_nested_dict = {
            'date': core_data.date.strftime('%Y-%m-%d'),
            'state': core_data.state,
            'meta': meta,
        }

        core_data_nested_dict.update(states_daily_simple_from_core_data(core_data))
        out['data'].append(core_data_nested_dict)

    response = flask.current_app.response_class(
        json.dumps(out, sort_keys=False, indent=2),
        mimetype=flask.current_app.config['JSONIFY_MIMETYPE'])
    return response
