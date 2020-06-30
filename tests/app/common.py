from datetime import datetime, date

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
    "negative": 5
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
    "negative": 4
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
      "coreData": [NY_TODAY, WA_TODAY, NY_YESTERDAY, WA_YESTERDAY]
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
      "coreData": [NY_YESTERDAY, WA_YESTERDAY]
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
      "coreData": [NY_TODAY, WA_TODAY]
    }

def edit_push_ny_yesterday():
    ctx = {
      "dataEntryType": "edit",
      "shiftLead": "test",
      "batchNote": "This is an edit test, incrementing NY count by 1"
    }

    return {
      "context": ctx,
      "coreData": [NY_YESTERDAY_EDITED]
    }