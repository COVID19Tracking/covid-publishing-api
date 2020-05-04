"""
TabCleaner -- transforms raw data from a tab using meta-data

This class supports:
    1. cleaning up the column names
    2. checking if the sheet is different from the meta-data
    3. limiting to requested columns
    4. type conversion of requested columns

Integer type conversion is tricky because there is no concept of an invalid value.
For our usage, I take -1000 (blank) and -1001 (invalid) as values.  If an invalid
value is encountered, I create an errors column that contains the unconverted value. - Josh E.

DateTime conversion is alway to eastern (for now)

TODO: Add Boolean and Date support

"""

from typing import List, Dict, Tuple
from loguru import logger
import pandas as pd
import numpy as np
import re

import data_convert.udatetime as udatetime


class TabCleaner:

    def __init__(self):
        pass

    # -- operations

    def cleanup_names(self, df:pd.DataFrame):
        """ remove extra whitespace column names 
        
        also names empty columns: col_1, col_2, col_3 etc.
        duplicate columns get a suffix of _1 ...
        """
        cols = []
        dups = {"col": 1}

        for n in df.columns:            
            #logger.debug(f"in = >>{n}<<")
            #n1 = n.replace("\r", "").replace("\n", " ")

            
            n1 = re.sub(r"\s+", " ", n)
            n1 = n1.replace('–', '-') # unicode em-dash
            n1 = n1.strip()

            if n1 == "": n1 = "col" 
            cnt = dups.get(n1)
            if cnt == None:
                dups[n1] = 1
            else:
                dups[n1] = cnt + 1
                n1 += "_" + str(cnt)

            #logger.debug(f"out = >>{n1}<<")
            cols.append(n1)

        df.columns = cols

    def check_names(self, df: pd.DataFrame, df_meta: pd.DataFrame) -> List:
        """
        Return a list of columns names that are not in expected locations.
        """

        #TODO: rewrite this as a output join and return a data table
        
        if df is None:
            raise Exception("Missing data frame")
        if df_meta is None:
            raise Exception("Missing meta-data")

        if not "name" in df_meta:
            raise Exception("Meta-Data should contain a 'name' column")

        expected_names = df_meta.name.values.tolist()

        # the 'fast' path -- nothing changes
        if df.columns.size == len(expected_names):
            is_diff = False
            for n1, n2 in zip(df.columns, expected_names):
                if n1 != n2: is_diff = True
            if not is_diff: return None 

        # the 'slow' path -- something changed 
        def find(xlist: List, name: str) -> int:
            name = name.lower()
            for j, name2 in enumerate(xlist):
                if name2.lower() == name: return j
            return -1
        def find2(xlist: List, name: str) -> int:
            name = name.lower()
            for j, pos_name in enumerate(xlist):
                if pos_name[1].lower() == name: return j
            return -1

        msgs = []

        # scan the found_names
        found_names = []
        for pos, name in enumerate(df.columns):
            j = find(expected_names, name)            
            if j < 0:
                msgs.append(f"Column {pos+1:02d}: {name} is a new column")
            else:
                name2 = expected_names[j]
                if name != name2:
                    msgs.append(f"Column {pos+1:02d}: {name} case changed")
                found_names.append((pos, name))

        # scan the expected_names
        matched_names = []
        for pos, name in enumerate(expected_names):
            j = find2(found_names, name)
            if j < 0:
                msgs.append(f"Column {pos+1:02d}: {name} is missing")
            else:
                matched_names.append((pos,name))

        # check for moved
        while len(found_names) > 0:
            pos1, name1 = found_names[0]
            _, name2 = matched_names[0]
            if name1.lower() == name2.lower():
                del found_names[0]
                del matched_names[0]            
            else:
                msgs.append(f"Column {pos1+1:02d}: {name1} has moved")
                del found_names[0]
                j = find2(matched_names, name1)
                del matched_names[j]            

        msgs.sort()
        return msgs

    def remap_names(self, df: pd.DataFrame, df_meta: pd.DataFrame) -> pd.DataFrame:
        """ returns a new frame containing output columns

        drop columns that don't have a mapping
        """

        if not "name" in df_meta.columns:
            raise Exception("Expected name in meta-data")
        if not "out_name" in df_meta.columns:
            raise Exception("Expected out_name in meta-data")

        # can't use panda's index easily because of missing values
        lookup = {}
        in_name = df_meta.name.tolist()
        out_name = df_meta.out_name.tolist()
        for xin, xout in zip(in_name, out_name):
            if xout is None or xout == "": continue
            lookup[xin] = xout

        df_new = pd.DataFrame()
        for n in df.columns:
            n2 = lookup.get(n)
            if n2 is None: continue
            df_new[n2] = df[n]
        return df_new

    def convert_types(self, df: pd.DataFrame, df_meta: pd.DataFrame):
        """ change all the types (in place) """

        if not "out_name" in df_meta.columns:
            raise Exception("Expected out_name in meta-data")
        if not "data_type" in df_meta.columns:
            raise Exception("Expected data_type in meta-data")

        df_meta = df_meta[ df_meta.out_name.fillna("") != ""  ]

        df_missing = df_meta[ pd.isnull(df_meta.data_type) ]
        if df_missing.shape[0] > 0:
            for i, xrow in df_missing.iterrows():
                logger.error(f"Missing data type for output column {xrow['out_name']}")
            raise Exception(f"Missing data_types for {df_missing.shape[0]} output columns")

        out_vec = df_meta.out_name.values
        type_vec = df_meta.data_type.values
        column_types = { xout: xtype for xout, xtype in zip(out_vec, type_vec) }

        for n in df.columns.values:
            t = column_types.get(n)
            if t == None:
                raise Exception(f"Missing output column for {n}")
            if t == "str": 
                pass
            elif t == "int":
                self.convert_to_int(df, n)
            elif t == "datetime":
                self.convert_to_date(df, n, as_eastern=True)
            else:
                raise Exception(f"Unsupported type ({t}), expected str, int, or datetime")


    # -------------------------

    def convert_to_int(self, df: pd.DataFrame, col_name: str):
        """ convert a series to int even if it contains bad data 
            blanks -> -1000
            errors -> -1001
        """

        # clean up the values (remove commas, fractions, whitespace)
        s = df[col_name].str.strip().str.replace(",", "").str.replace(r"\\.[0-9][0-9]?$", "")
        df[col_name] = s

        # set blanks to -1000
        is_blank = (s == "")
        df.loc[is_blank, col_name] = "-1000"

        # find anything that is bad, trace, set it to -1001
        s = df[col_name]
        is_bad = (~s.str.isnumeric() & ~is_blank)

        df_errs = df[is_bad][[col_name]]
        if df_errs.shape[0] != 0: 
            logger.error(f"invalid input values for {col_name}:\n{df_errs}")
            for _, e_row in df_errs.iterrows():
                v = e_row[col_name]
                logger.error(f"Invalid {col_name} value ({v}) for {e_row.state}")

            s = s.where(is_bad, other="-1001")
            df[col_name] = s

        # convert to int
        df[col_name] = df[col_name].astype(np.int)


    def convert_to_date(self, df: pd.DataFrame, name: str, as_eastern: bool):
        " convert a series to a panda's datetime"

        def standardize_date(d: str) -> str:
            sd, err_num = udatetime.standardize_date(d)
            return str(err_num) + sd

        s = df[name]
        s_date = s.apply(standardize_date)

        s_idx = s_date.str[0].astype(np.int)
        names = ["", "changed", "blank", "missing date", "missing time", "bad date", "bad time"]
        s_msg = s_idx.map(lambda x: names[x])

        s_date = s_date.str[1:]

        s_date = pd.to_datetime(s_date, format="%m/%d/%Y %H:%M")
        if as_eastern:
            s_date = s_date.apply(udatetime.pandas_timestamp_as_eastern)

        df[name] = s_date
        df[name + "_msg"] = s_msg

