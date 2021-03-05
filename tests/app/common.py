from datetime import datetime, date, timedelta
import pytz

BEFORE_YESTERDAY = date(2020, 5, 20)
YESTERDAY = date(2020, 5, 24)
TODAY = date(2020, 5, 25)
NOW = pytz.utc.localize(datetime.now())
MARCH7 = date(2021, 3, 7)
MARCH8 = date(2021, 3, 8)

NY = {"state": "NY", "totalTestResultsFieldDbColumn": "posNeg"}
CA_DIFFERENT_TOTAL_SOURCE = {"state": "CA", "totalTestResultsFieldDbColumn": "totalTestsViral"}
WA = {"state": "WA", "totalTestResultsFieldDbColumn": "posNeg"}

NY_TODAY = {
    "state": "NY",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": TODAY,
    "positive": 20,
    "negative": 5,
    "inIcuCurrently": 33
}

NY_YESTERDAY = {
    "state": "NY",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": YESTERDAY,
    "positive": 15,
    "negative": 4,
    "inIcuCurrently": 37
}

NY_MARCH7 = {
    "state": "NY",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": MARCH7,
    "positive": 15,
    "negative": 4,
    "inIcuCurrently": 37
}

NY_MARCH8 = {
    "state": "NY",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": MARCH8,
    "positive": 16,
    "negative": 4,
    "inIcuCurrently": 35
}

WA_TODAY = {
    "state": "WA",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": TODAY,
    "positive": 10,
    "negative": 10
}

WA_YESTERDAY = {
    "state": "WA",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": YESTERDAY,
    "positive": 9,
    "negative": 8
}

WA_MARCH7 = {
    "state": "WA",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": MARCH7,
    "positive": 10,
    "negative": 10
}

WA_MARCH8 = {
    "state": "WA",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": MARCH8,
    "positive": 11,
    "negative": 11
}

# edit to increase positive count by 1
# remove inIcuCurrently
NY_YESTERDAY_EDITED = {
    "state": "NY",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": YESTERDAY,
    "positive": 16,
    "negative": 4,
    "inIcuCurrently": None
}

# edit to increase positive count by 1
# do not send other fields
NY_YESTERDAY_PARTIAL_EDIT = {
    "state": "NY",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": YESTERDAY,
    "positive": 16
}

NY_TODAY_EDITED = {
    "state": "NY",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": TODAY,
    "positive": 20,
    "negative": 5,
    "inIcuCurrently": 35
}

NY_BEFORE_YESTERDAY = {
    "state": "NY",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": BEFORE_YESTERDAY,
    "positive": 10,
    "negative": 2
}

CA_TODAY = {
    "state": "CA",
    "lastUpdateIsoUtc": NOW.isoformat(),
    "dateChecked": NOW.isoformat(),
    "date": TODAY,
    "positive": 10,
    "negative": 5
}

# Test data used for testing US daily and states daily by state
def daily_push_ny_wa_two_days():
    ctx = {
      "dataEntryType": "daily",
      "shiftLead": "test",
      "batchNote": "This is a test"
    }

    return {
      "context": ctx,
      "states": [NY, WA],
      "coreData": [NY_TODAY.copy(), WA_TODAY.copy(), NY_YESTERDAY.copy(), WA_YESTERDAY.copy()]
    }

def daily_push_ny_ca_total_test_results_different_source():
    ctx = {
      "dataEntryType": "daily",
      "shiftLead": "test",
      "batchNote": "This is a test with a different totalTestResults source for CA"
    }

    return {
      "context": ctx,
      "states": [NY, WA, CA_DIFFERENT_TOTAL_SOURCE],
      "coreData": [
          NY_TODAY.copy(), WA_TODAY.copy(), NY_YESTERDAY.copy(), WA_YESTERDAY.copy(),
          CA_TODAY.copy()
      ]
    }

def daily_push_ny_wa_yesterday():
    ctx = {
      "dataEntryType": "daily",
      "shiftLead": "test",
      "batchNote": "This is a test"
    }

    return {
      "context": ctx,
      "states": [NY, WA],
      "coreData": [NY_YESTERDAY.copy(), WA_YESTERDAY.copy()]
    }

def daily_push_ny_wa_today():
    ctx = {
      "dataEntryType": "daily",
      "shiftLead": "test",
      "batchNote": "This is a test"
    }

    return {
      "context": ctx,
      "states": [NY, WA],
      "coreData": [NY_TODAY.copy(), WA_TODAY.copy()]
    }

def daily_push_ny_wa_march_2021():
    ctx = {
      "dataEntryType": "daily",
      "shiftLead": "test",
      "batchNote": "This is a future test"
    }

    return {
      "context": ctx,
      "states": [NY, WA],
      "coreData": [NY_MARCH7.copy(), NY_MARCH8.copy(), WA_MARCH7.copy(), WA_MARCH8.copy()]
    }

def edit_push_ny_yesterday():
    ctx = {
      "dataEntryType": "edit",
      "shiftLead": "test",
      "batchNote": "This is an edit test, incrementing NY count by 1"
    }

    return {
      "context": ctx,
      "coreData": [NY_YESTERDAY_EDITED.copy()]
    }

# Simulate a States Daily push where we may receive unedited rows. Include state in context
def edit_push_ny_yesterday_unchanged_today():
    ctx = {
      "dataEntryType": "edit",
      "shiftLead": "test",
      "state": "NY",
      "batchNote": "This is an edit test, incrementing NY count by 1, leaving NY today alone",
      "logCategory": "State Updates",
      "link": "https://example.com"
    }

    return {
      "context": ctx,
      "coreData": [NY_YESTERDAY_EDITED.copy(), NY_TODAY.copy()]
    }

def edit_push_ny_yesterday_change_only_timestamp():
    ctx = {
      "dataEntryType": "edit",
      "shiftLead": "test",
      "state": "NY",
      "batchNote": "This is an edit test changing only the timestamp",
      "logCategory": "State Updates",
      "link": "https://example.com"
    }

    edit_data = NY_TODAY.copy()
    edit_data['lastUpdateIsoUtc'] = (NOW - timedelta(days=1)).isoformat()

    return {
      "context": ctx,
      "coreData": [edit_data]
    }

def edit_push_ny_yesterday_change_only_positive():
    ctx = {
      "dataEntryType": "edit",
      "shiftLead": "test",
      "state": "NY",
      "batchNote": "This is an edit test changing only the positive val",
      "logCategory": "State Updates",
      "link": "https://example.com"
    }

    return {
      "context": ctx,
      "coreData": [NY_YESTERDAY_PARTIAL_EDIT.copy()]
    }

def edit_push_ny_today_and_before_yesterday():
    ctx = {
      "dataEntryType": "edit",
      "shiftLead": "test",
      "state": "NY",
      "batchNote": "This is an edit test with two dates",
      "logCategory": "State Updates",
      "link": "https://example.com"
    }

    return {
      "context": ctx,
      "coreData": [NY_TODAY_EDITED.copy(), NY_BEFORE_YESTERDAY.copy()]
    }


def edit_push_multiple_states():
    ctx = {
      "dataEntryType": "edit",
      "shiftLead": "test",
      "state": "NY",
      "batchNote": "This is an edit test that should fail because it contains >1 state"
    }

    return {
      "context": ctx,
      "coreData": [NY_YESTERDAY_EDITED.copy(), WA_YESTERDAY.copy()]
    }

def edit_push_ny_today_empty():
    ctx = {
      "dataEntryType": "edit",
      "shiftLead": "test",
      "state": "NY",
      "batchNote": "No changes",
      "logCategory": "State Updates",
      "link": "https://example.com"
    }

    edit_data = {
        "state": "NY",
        "date": TODAY
    }

    return {
      "context": ctx,
      "coreData": [edit_data]
    }

def edit_unknown_fields():
    ctx = {
      "dataEntryType": "edit",
      "shiftLead": "test",
      "state": "NY",
      "batchNote": "no data",
      "logCategory": "State Updates",
      "link": "https://example.com"
    }

    edit_data = {
      "state": "NY",
      "date": BEFORE_YESTERDAY,
      "foobar": 1
    }

    return {
      "context": ctx,
      "coreData": [edit_data]
    }
