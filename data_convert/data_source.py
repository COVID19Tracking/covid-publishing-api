"""
DataSource manages access to the tabs of the google worksheet.

Right now, we map two tabs: working and checks.  Working is the 
main (unpublished) data entry tab.  Checks is the history of publish.

The data source acts as a cache and loads the data on first access.

"""
from typing import List, Dict
from loguru import logger
import pandas as pd
import socket

from data_convert.tab_working import TabWorking
from data_convert.tab_checks import TabChecks


class DataSource:

    def __init__(self):
        self._working: TabWorking = TabWorking()
        self._checks: TabChecks = TabChecks()

    @property
    def working(self) -> pd.DataFrame:
        " the working tab from the google sheet"

        df = self._working.df
        if df is None:
            df = self._working.load()
        return df

    @property
    def checks(self) -> pd.DataFrame:
        " the checks tab from the google sheet"

        df = self._checks.df
        if df is None:
            df = self._checks.load()
        return df

    def clear(self):
        " clears the cache"
        self._working.clear()
        self._checks.clear()


# ------------------------------------------------------------
def main():

    ds = DataSource()
    logger.info(f"working\n{ds.working.to_json(orient='table', indent=2)}")
    #logger.info(f"checks\n{ds.checks.df.info()}")


if __name__ == '__main__':
    main()
