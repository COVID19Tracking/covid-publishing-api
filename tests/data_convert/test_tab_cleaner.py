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

def test_check_names():

    cleaner = TabCleaner()

    df_meta = pd.DataFrame([
        {"name": "a"},
        {"name": "b"},
        {"name": "c"},
        {"name": "d"},
    ])

    # normal
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3], "d": [4]})
    msgs = cleaner.check_names(df, df_meta)
    assert(msgs is None)

    # extra
    df = pd.DataFrame({"x": [0], "a": [1], "b": [2], "y": [0], "c": [3], "d": [4], "z": [0]})
    msgs = cleaner.check_names(df, df_meta)
    assert(msgs == ['Column 01: x is a new column', 'Column 04: y is a new column', 'Column 07: z is a new column'])    

    # moved
    df = pd.DataFrame({"a": [1], "c": [3], "b": [2], "d": [4]})
    msgs = cleaner.check_names(df, df_meta)
    assert(msgs == ['Column 02: c has moved'])

    df = pd.DataFrame({"a": [1], "x": [0], "c": [3], "d": [4], "b": [2]})
    msgs = cleaner.check_names(df, df_meta)
    assert(msgs == ['Column 02: x is a new column', 'Column 03: c has moved', 'Column 04: d has moved'])

    # missing
    df = pd.DataFrame({"a": [1], "c": [3], "d": [4]})
    msgs = cleaner.check_names(df, df_meta)
    assert(msgs == ['Column 02: b is missing'])

    df = pd.DataFrame({"a": [1], "c": [3]})
    msgs = cleaner.check_names(df, df_meta)
    assert(msgs == ['Column 02: b is missing', 'Column 04: d is missing'])

    df = pd.DataFrame({"c": [3], "d": [4]})
    msgs = cleaner.check_names(df, df_meta)
    assert(msgs == ['Column 01: a is missing', 'Column 02: b is missing'])

def test_remap_names():

    cleaner = TabCleaner()

    df_meta = pd.DataFrame([
        {"name": "a", "out_name": "a"},
        {"name": "b", "out_name": ""},
        {"name": "c", "out_name": "x"},
        {"name": "d", "out_name": None},
    ])

    df = pd.DataFrame({"a": [1], "b": [2], "c": [3], "d": [4]})
    df = cleaner.remap_names(df, df_meta)
    assert(df.columns.tolist() == ["a", "x"])

    #TODO: test fail on duplicate outputs

def test_convert_types():

    cleaner = TabCleaner()

    df_meta = pd.DataFrame([
        {"name": "a", "out_name": "a", "data_type": "str"},
        {"name": "b", "out_name": "b", "data_type": "int"},
        {"name": "c", "out_name": "c", "data_type": "datetime"},
        {"name": "d", "out_name": None, "data_type": None},
        {"name": "e", "out_name": "", "data_type": None}
    ])

    df = pd.DataFrame({"a": ["x", "y", "z"], "b": ["0", "1,000", ""], "c": ["3/1/20", "3/1/20 13:30", "3/1/20 01:20"]})
    cleaner.convert_types(df, df_meta)

    assert(type(df.a[0]) == str)
    assert(df.a.tolist() == ["x", "y", "z"])

    assert(type(df.b[0]) == np.int32)
    assert(df.b.tolist() == [0, 1000, -1000])

    assert(str(df.c.dtype) == "datetime64[ns, US/Eastern]")
    assert(df.c.astype(str).tolist() == ["2020-03-01 00:00:00-05:00", "2020-03-01 13:30:00-05:00", "2020-03-01 01:20:00-05:00"])

    #TODO: Test bad int failure.
