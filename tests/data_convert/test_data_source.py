from data_convert.data_source import DataSource
import pandas as pd


def test_working():

    ds = DataSource()

    df_working = ds.working
    print(df_working)

    assert(not (df_working is None))
    assert(len(df_working) == 56)


def test_states():

    ds = DataSource()

    df_states = ds.states
    print(df_states)

    assert(not (df_states is None))
    assert(len(df_states) == 56)    