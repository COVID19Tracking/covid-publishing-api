import pandas as pd
import numpy as np
from data_convert.tab_cleaner import TabCleaner

def test_cleanup_names():

    cleaner = TabCleaner()

    df = pd.DataFrame({
        "  name  \t  1\t  ": [1],
        " name\n2  ": [1],
        " ": [1],
        "   ": [1],
        " a": [1],
        " a  ": [1],
    })

    cleaner.cleanup_names(df)

    assert(df.columns[0] == "name 1")
    assert(df.columns[1] == "name 2")
    assert(df.columns[2] == "col_1")
    assert(df.columns[3] == "col_2")
    assert(df.columns[4] == "a")
    assert(df.columns[5] == "a_1")

def test_find_changes():

    cleaner = TabCleaner()

    df_meta = pd.DataFrame([
        {"name": "a"},
        {"name": "b"},
        {"name": "c"},
        {"name": "d"},
    ])

    # same
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3], "d": [4]})
    df_changed = cleaner.find_changes(df, df_meta)
    assert(df_changed is None)

    # added
    df = pd.DataFrame({"x": [0], "a": [1], "b": [2], "y": [0], "c": [3], "d": [4], "z": [0]})
    df_changed = cleaner.find_changes(df, df_meta)
    assert(not (df_changed is None))
    assert(df_changed.shape[0] == 7)
    assert(df_changed.current[0] == 'x')
    assert(df_changed.expected[0] == 'a')
    assert(df_changed.expected[6] == '')

    # less
    df = pd.DataFrame({"b": [2], "c": [3]})
    df_changed = cleaner.find_changes(df, df_meta)
    assert(not (df_changed is None))
    assert(df_changed.shape[0] == 4)
    assert(df_changed.current[0] == 'b')
    assert(df_changed.current[3] == '')


def test_remap_names():

    cleaner = TabCleaner()

    df_meta = pd.DataFrame([
        {"name": "a", "outName": "a"},
        {"name": "b", "outName": ""},
        {"name": "c", "outName": "x"},
        {"name": "d", "outName": None},
    ])

    df = pd.DataFrame({"a": [1], "b": [2], "c": [3], "d": [4]})
    df = cleaner.remap_names(df, df_meta)
    assert(df.columns.tolist() == ["a", "x"])

    #TODO: test fail on duplicate outputs

def test_convert_types():

    cleaner = TabCleaner()

    df_meta = pd.DataFrame([
        {"name": "a", "outName": "a", "dataType": "str"},
        {"name": "b", "outName": "b", "dataType": "int"},
        {"name": "c", "outName": "c", "dataType": "datetime"},
        {"name": "d", "outName": None, "dataType": None},
        {"name": "e", "outName": "", "dataType": None}
    ])

    df = pd.DataFrame({"a": ["x", "y", "z"], "b": ["0", "1,000", ""], "c": ["3/1/20", "3/1/20 13:30", "3/1/20 01:20"]})
    cleaner.convert_types(df, df_meta)

    assert(type(df.a[0]) == str)
    assert(df.a.tolist() == ["x", "y", "z"])

    assert(type(df.b[0]) == np.int64 or type(df.b[0]) == np.int32)
    assert(df.b.tolist() == [0, 1000, -1000])

    assert(str(df.c.dtype) == "datetime64[ns, US/Eastern]")
    assert(df.c.astype(str).tolist() == ["2020-03-01 00:00:00-05:00", "2020-03-01 13:30:00-05:00", "2020-03-01 01:20:00-05:00"])

    #TODO: Test bad int failure.
