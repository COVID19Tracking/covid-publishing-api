"""
Wrapper around GoogleSheets

Provides three main functions:
    1. assigns a symbolic name to a worksheet so the rest of the code doesn't depend 
    on a specific address.
    2. read the content of the URL into a data frame
    3. extract of region from the frame
"""

from typing import List, Dict, Tuple
from loguru import logger
import pandas as pd
import numpy as np
import re
import io

import requests


class WorksheetWrapper():

    def __init__(self, debug = True):
        pass
        
    def get_sheet_url(self, name: str) -> str:
        "get the id for a worksheet by symbolic name"
        items = {
            "working": {
                "id": "1MvvbHfnjF67GnYUDJJiNYUmGco5KQ9PW0ZRnEP9ndlU",
                "url": "https://docs.google.com/spreadsheets/d/1MvvbHfnjF67GnYUDJJiNYUmGco5KQ9PW0ZRnEP9ndlU/export?format=csv&gid=2335020"
            },
            "states": {
                "id": "1MvvbHfnjF67GnYUDJJiNYUmGco5KQ9PW0ZRnEP9ndlU",
                "url": "https://docs.google.com/spreadsheets/d/1MvvbHfnjF67GnYUDJJiNYUmGco5KQ9PW0ZRnEP9ndlU/export?format=csv&gid=1208387230"
            },
            "checks": {
                "id": "1MvvbHfnjF67GnYUDJJiNYUmGco5KQ9PW0ZRnEP9ndlU",
                "url": "https://docs.google.com/spreadsheets/d/1MvvbHfnjF67GnYUDJJiNYUmGco5KQ9PW0ZRnEP9ndlU/export?format=csv&gid=355296281"
            }
        }

        rec = items.get(name)
        if rec == None:
            raise Exception(f"Invalid name {name}, should be one of " + ", ".join([x for x in items]))
        return rec["url"]

    def generate_column_names(self, cnt: int) -> List[str]:
        "generate column names of a spreadsheet"
        n = "A"
        result = []
        for _ in range(cnt):
            result.append(n)

            x = n[-1]
            if x < "Z":                
                x = chr(ord(x) + 1)
                n = n[0] + x if len(n) > 1 else x
            else:
                x = chr(ord(n[0])+1) if len(n) > 1 else "A"
                n = x + "A"
        return result

    def download_data(self, url: str) -> pd.DataFrame:
        "download content from a url"
        response = requests.get(url)
        content = response.content

        f = io.StringIO(content.decode())        
        df = pd.read_csv(f, sep=",", header=None, dtype=str )
        df.fillna("", inplace=True)
        df.columns = self.generate_column_names(df.shape[1])
        return df

    def parse_range(self, arange: str) -> Tuple[Tuple, Tuple]:
        " parse a spreadsheet range"
        
        if arange == None:
            raise Exception("Missing arange argument")

        m = re.match(r"([A-Z]+)([0-9]+):([A-Z]+)([0-9]+)", arange)
        if not m: raise Exception(f"Invalid arange ({arange})")

        xstart = m[1], int(m[2])-1
        xstop = m[3], int(m[4])-1
        return xstart, xstop

    def read_values(self, df: pd.DataFrame, cell_range: str) -> pd.DataFrame:
        """" 
        read a region of the sheet 
        
        returns a data frame
        """

        xstart, xstop = self.parse_range(cell_range)

        row_filter = (df.index >= xstart[1]) & (df.index <= xstop[1])

        cols = df.columns.tolist()
        sidx = cols.index(xstart[0])
        eidx = cols.index(xstop[0])
        col_filter = df.columns[sidx:eidx+1]

        df = df[row_filter][col_filter]
        return df


    def read_as_list(self, df: pd.DataFrame, cell_range: str, ignore_blank_cells=False, single_row=False) -> List:
        """
        read a region of a sheet as a simple list or a list of list
        
        has an option to ignore blank cells
        has an option to return a single row
        """
        df = self.read_values(df, cell_range)

        result = []
        for _, row in df.iterrows():
            row_list = [x for x in row if x != "" or not ignore_blank_cells]
            if len(row_list) > 0 or not ignore_blank_cells:
                result.append(row_list)

        if single_row and len(result) > 0: result = result[0]
        return result

    def read_as_frame(self, df: pd.DataFrame, cell_range: str, header_rows = 1) -> pd.DataFrame:
        """
        read a region of a sheet as a data frame
        
        first row(s) are used as the column names
        if there are more than one header row, the rows are combined to form the name

        returns a data frame
        """

        df = self.read_values(df, cell_range)

        header = df.iloc[0].tolist()
        if header_rows == 2:
            sub_header = df.iloc[1].tolist()
            prefix = ""
            for i in range(len(sub_header)):
                if i<len(header):
                    if header[i].strip() != "": prefix = header[i].strip()  + " "
                else:
                    prefix = ""
                sub_header[i] = prefix + sub_header[i].strip()
            header = sub_header
        else:
            for i in range(len(header)): header[i] = header[i].strip()

        df = df[header_rows:].copy().reset_index(drop=True)
        df.columns = header
        return df