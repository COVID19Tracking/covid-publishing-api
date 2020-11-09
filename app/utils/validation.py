"""Validation module for various API methods. """

from app.models.data import *


def validate_non_empty_fields(payload):
    # check non-empty fields
    core_data_dicts = payload['coreData']
    required_fields = ['state', 'date']
    for core_data_dict in core_data_dicts:
        for field in required_fields:
            # should fail if missing field or empty string
            if not core_data_dict.get(field):
                raise ValueError(f"Missing value for '{field}' in row: {core_data_dict}")


def validate_numeric_fields(payload):
    # validate data fields: check that all numeric fields, if not null, are numeric and non-negative
    numeric_fields = CoreData.numeric_fields()
    core_data_dicts = payload['coreData']
    for core_data_dict in core_data_dicts:
        for field in numeric_fields:
            value = core_data_dict.get(field)
            state = core_data_dict.get('state')
            if value is not None:
                # if not an integer, error out
                try:
                    int_value = int(value)
                except ValueError:
                    raise ValueError(f"Non-numeric value for field '{state} {field}': {value}")
                # if negative integer, error out
                if int_value < 0:
                    raise ValueError(f"Negative value for field '{state} {field}': {value}")


def validate_no_unknown_fields(payload):
    core_data_dicts = payload['coreData']
    for core_data_dict in core_data_dicts:
        _, unknown = CoreData.valid_fields_checker(core_data_dict)
        # lastUpdateIsoUtc can come in as an argument, gets converted to lastUpdateTime internally;
        # we don't error on its presence
        unknown.discard('lastUpdateIsoUtc')
        if unknown:
            raise ValueError("Unknown field(s) in CoreData: %s" % ', '.join(unknown))


# Returns a string with any errors if the payload is invalid, otherwise returns empty string.
def validate_core_data_payload(payload):
    # test the input data
    if 'context' not in payload:
        raise ValueError("Payload requires 'context' field")
    if 'states' not in payload or not payload['states']:
        raise ValueError("Payload requires 'states' field with at least one entry")
    if 'coreData' not in payload or not payload['coreData']:
        raise ValueError("Payload requires 'coreData' field with at least one entry")

    validate_numeric_fields(payload)
    validate_non_empty_fields(payload)    
    validate_no_unknown_fields(payload)


# Returns a string with any errors if the payload is invalid, otherwise returns empty string.
def validate_edit_data_payload(payload):
    # check push context
    if 'context' not in payload:
        raise ValueError("Payload requires 'context' field")

    context = payload['context']
    if context['dataEntryType'] != 'edit':
        raise ValueError("Payload 'context' must contain data entry type 'edit'")
    if not context.get('batchNote'):
        raise ValueError("Payload 'context' must contain a batchNote explaining edit")
    if not context.get('state'):
        raise ValueError("No state specified in batch edit context")

    # check that edit data exists and that there's at least one row
    if 'coreData' not in payload or not payload['coreData']:
        raise ValueError("Payload requires 'coreData' field with at least one entry")

    validate_numeric_fields(payload)
    validate_non_empty_fields(payload)
    validate_no_unknown_fields(payload)

    # check that the context state matches JSON data state, of which there should be only one
    context_state = context['state']
    data_state_set = set([x.get('state') for x in payload['coreData']])
    if len(data_state_set) > 1:
        raise ValueError("Multiple states in edit request, only 1 expected: %s" % data_state_set)

    data_state = list(data_state_set)[0]
    if context_state != data_state:
        raise ValueError(
            f"Context state {context_state} does not match JSON data state {data_state}")
