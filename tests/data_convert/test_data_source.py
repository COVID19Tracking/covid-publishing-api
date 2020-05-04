from data_convert.data_source import DataSource
import pandas as pd


def test_working():

    ds = DataSource()

    df_working = ds.working
    assert(not (df_working is None))
    assert(len(df_working) == 56)

    print(df_working)


