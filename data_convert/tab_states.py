"""
TabStates -- Load data from the states tab
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


class TabStates(TabBase):

    def __init__(self):
        super(TabStates, self).__init__()


    def _load_metadata(self) -> pd.DataFrame:
        xdir = os.path.dirname(__file__)
        xpath = os.path.join(xdir, "meta_states.json")
        if not os.path.exists(xpath):
            raise Exception(f"Missing meta-data file: {xpath}")
        return pd.read_json(xpath)


    def _load_content(self) -> pd.DataFrame:
        """Load the states tab from google sheets"""

        gs = WorksheetWrapper()
        url = gs.get_sheet_url("states")

        df = gs.download_data(url)
        df = gs.read_as_frame(df, "A1:L57", header_rows=1)

        # cleanup logic
        cleaner = TabCleaner()
        cleaner.cleanup_names(df)

        df_meta_data = self.metadata()
        if df_meta_data is None:
            raise Exception("Meta-data not available")

        df_changed = cleaner.find_changes(df, df_meta_data)
        if not (df_changed is None):
            pd.set_option('display.max_rows', None)
            logger.error(f"Names are\n{df_changed}")
            raise Exception("Meta-data is out-of-date")

        df = cleaner.remap_names(df, df_meta_data)

        #cleaner.convert_types(df, df_meta_data)

        df = df[ df.state != ""]
        return df


# ------------------------------------------------------------
def main():

    tab = TabStates()
    tab.load()

    logger.info(f"working\n{tab.df.to_json(orient='table', indent=2)}")


if __name__ == '__main__':
    main()
