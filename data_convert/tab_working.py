"""
TabWorking -- Load data from the worrking tab (Sheet 2)
"""

from typing import List, Dict
from loguru import logger
import pandas as pd
from urllib.request import urlopen
import json
import numpy as np
import re
import os
import requests
import socket
import io

import data_convert.udatetime
from data_convert.worksheet_wrapper import WorksheetWrapper
from data_convert.tab_base import TabBase
from data_convert.tab_cleaner import TabCleaner


class TabWorking(TabBase):

    def __init__(self):
        super(TabWorking, self).__init__()

        # worksheet dates from top row
        self.last_publish_time = ""
        self.last_push_time = ""
        self.current_time = ""


    def parse_dates(self, dates: List):
        if len(dates) != 5:
            raise Exception("First row layout (containing dates) changed")
        last_publish_label, last_publish_value, last_push_label, \
            last_push_value, current_time_field = dates

        if last_publish_label != "Last Publish Time:":
            raise Exception("Last Publish Time (cells V1:U1) moved")
        if last_push_label != "Last Push Time:":
            raise Exception("Last Push Time (cells Z1:AA1) moved")
        if not current_time_field.startswith("CURRENT TIME: "):
            raise Exception("CURRENT TIME (cell AG1) moved")

        self.last_publish_time = last_publish_value
        self.last_push_time = last_push_value
        self.current_time = current_time_field[current_time_field.index(":")+1:].strip()


    def _load_metadata(self) -> pd.DataFrame:
        xdir = os.path.dirname(__file__)
        xpath = os.path.join(xdir, "meta_working.json")
        if not os.path.exists(xpath):
            raise Exception(f"Missing meta-data file: {xpath}")
        return pd.read_json(xpath)


    def _load_content(self) -> pd.DataFrame:
        """Load the working (unpublished) data from google sheets"""

        gs = WorksheetWrapper()
        dev_id = gs.get_sheet_id_by_name("dev")

        dates = gs.read_as_list(dev_id, "Worksheet 2!W1:AN1", ignore_blank_cells=True, single_row=True)
        self.parse_dates(dates)

        df = gs.read_as_frame(dev_id, "Worksheet 2!A2:BR60", header_rows=1)

        # cleanup logic
        cleaner = TabCleaner()
        cleaner.cleanup_names(df)

        df_meta_data = self.metadata()
        if df_meta_data is None:
            raise Exception("Meta-data not available")

        msgs = cleaner.check_names(df, df_meta_data)
        if not (msgs is None):
            for m in msgs:
                logger.error(m)
            logger.error(f"Column names are:{df.columns}")
            raise Exception("Meta-data is out-of-date")

        df = cleaner.remap_names(df, df_meta_data)

        cleaner.convert_types(df, df_meta_data)

        df = df[ df.state != ""]
        return df


# ------------------------------------------------------------
def main():

    tab = TabWorking()
    tab.load()

    logger.info(f"working\n{tab.df.to_json(orient='table', indent=2)}")


if __name__ == '__main__':
    main()
