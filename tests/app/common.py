from datetime import datetime, date

BEFORE_YESTERDAY = date(2020, 5, 20)
YESTERDAY = date(2020, 5, 24)
TODAY = date(2020, 5, 25)

NY = {"state": "NY"}
WA = {"state": "WA"}

NY_TODAY = {
    "state": "NY",
    "lastUpdateIsoUtc": datetime.now().isoformat(),
    "dateChecked": datetime.now().isoformat(),
    "date": TODAY,
    "positive": 20,
    "negative": 5,
    "inIcuCurrently": 33
}

WA_TODAY = {
    "state": "WA",
    "lastUpdateIsoUtc": datetime.now().isoformat(),
    "dateChecked": datetime.now().isoformat(),
    "date": TODAY,
    "positive": 10,
    "negative": 10
}

NY_YESTERDAY = {
    "state": "NY",
    "lastUpdateIsoUtc": datetime.now().isoformat(),
    "dateChecked": datetime.now().isoformat(),
    "date": YESTERDAY,
    "positive": 15,
    "negative": 4,
    "inIcuCurrently": 37
}

WA_YESTERDAY = {
    "state": "WA",
    "lastUpdateIsoUtc": datetime.now().isoformat(),
    "dateChecked": datetime.now().isoformat(),
    "date": YESTERDAY,
    "positive": 9,
    "negative": 8
}

# edit to increase positive count by 1
NY_YESTERDAY_EDITED = {
    "state": "NY",
    "lastUpdateIsoUtc": datetime.now().isoformat(),
    "dateChecked": datetime.now().isoformat(),
    "date": YESTERDAY,
    "positive": 16,
    "negative": 4
}

NY_TODAY_EDITED = {
    "state": "NY",
    "lastUpdateIsoUtc": datetime.now().isoformat(),
    "dateChecked": datetime.now().isoformat(),
    "date": TODAY,
    "positive": 20,
    "negative": 5,
    "inIcuCurrently": 35
}

NY_BEFORE_YESTERDAY = {
    "state": "NY",
    "lastUpdateIsoUtc": datetime.now().isoformat(),
    "dateChecked": datetime.now().isoformat(),
    "date": BEFORE_YESTERDAY,
    "positive": 10,
    "negative": 2
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
