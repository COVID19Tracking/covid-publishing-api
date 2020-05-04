"""
TabBase is the base class for each tab in the spreadsheet.

It has both data (from the sheet) and metadata (stored in a .json file for now)

Each tab implementation is expected to implement two load method.

The meta-data load typically reads a json file but could easily read from a database.

The data load is expected to read from the sheet and use the TabCleaner to apply the
meta-data naming and type transformations to the raw data. 

"""
from abc import abstractclassmethod, ABC
from loguru import logger
import pandas as pd
import numpy as np
import socket


class TabBase(ABC):

    def __init__(self):
        self._df: pd.DataFrame = None
        self._df_meta: pd.DataFrame = None

    @property
    def df(self) -> pd.DataFrame:
        "returns the data"
        return self._df

    def metadata(self) -> pd.DataFrame:
        "return the meta-data"
        return self._df_meta

    def load(self) -> pd.DataFrame:
        "load the data"
        try:
            self._df_meta = self._load_metadata()
            self._df = self._load_content()
            return self._df
        except socket.timeout:
            logger.error(f"Could not fetch tab")
            return None
        except Exception as ex:
            logger.exception(ex)                
            logger.error(f"Could not load tab", exception=ex)
            return None

    def clear(self):
        "clear the cache"
        self._df = None
        self._df_meta = None

    @abstractclassmethod
    def _load_metadata(self) -> pd.DataFrame:
        "implements the tab-specific meta-data load"
        pass

    @abstractclassmethod
    def _load_content(self) -> pd.DataFrame:
        "implements the tab-specific data load"
        pass

