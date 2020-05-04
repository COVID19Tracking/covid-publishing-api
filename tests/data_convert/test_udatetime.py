import data_convert.udatetime as ud
import pandas as pd
import numpy as np


def test_standardize_date():

    d, e = ud.standardize_date("03/01/2020 00:00")
    assert(d == "03/01/2020 00:00")
    assert(e == 0)
    d, e = ud.standardize_date("3/1/20")
    assert(d == "03/01/2020 00:00")
    assert(e == 0)
    d, e = ud.standardize_date("03/1/20")
    assert(d == "03/01/2020 00:00")
    assert(e == 0)
    d, e = ud.standardize_date("3/01/20")
    assert(d == "03/01/2020 00:00")
    assert(e == 0)

    d, e = ud.standardize_date("03/01/2020 12:30")
    assert(d == "03/01/2020 12:30")
    assert(e == 0)

def test_pandas_timestamp_as_eastern():

    df = pd.DataFrame({"sdate": ["03/01/2020 12:30"]})
    assert(type(df.sdate.values[0]) == str)

    x_date = pd.to_datetime(df.sdate, format="%m/%d/%Y %H:%M")
    x_date = x_date.apply(ud.pandas_timestamp_as_eastern)
    assert(str(x_date.dtype) == "datetime64[ns, US/Eastern]")
