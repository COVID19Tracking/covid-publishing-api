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


# Returns a string with any errors if the payload is invalid, otherwise returns empty string.
def validate_core_data_payload(payload):
    # test the input data
    if 'context' not in payload:
        raise ValueError("Payload requires 'context' field")
    if 'states' not in payload:
        raise ValueError("Payload requires 'states' field")
    if 'coreData' not in payload:
        raise ValueError("Payload requires 'coreData' field")

    validate_numeric_fields(payload)
    validate_non_empty_fields(payload)    


# Returns a string with any errors if the payload is invalid, otherwise returns empty string.
def validate_edit_data_payload(payload):
    # check push context
    if 'context' not in payload:
        raise ValueError("Payload requires 'context' field")
    if payload['context']['dataEntryType'] != 'edit':
        raise ValueError("Payload 'context' must contain data entry type 'edit'")
    if not payload['context'].get('batchNote'):
        raise ValueError("Payload 'context' must contain a batchNote explaining edit")

    # check that edit data exists
    if 'coreData' not in payload:
        raise ValueError("Payload requires 'coreData' field")

    validate_numeric_fields(payload)
    validate_non_empty_fields(payload)
