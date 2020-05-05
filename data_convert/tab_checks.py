"""
TabChecks -- Load data from the checks tab

NOT IMPLEMENTED YET
"""

import os
import pandas as pd
from loguru import logger

from datetime import datetime

#import state_abbrevs
import data_convert.udatetime

from data_convert.worksheet_wrapper import WorksheetWrapper

from data_convert.tab_base import TabBase
from data_convert.tab_cleaner import TabCleaner


class TabChecks(TabBase):

    def __init__(self):
        super(TabChecks, self).__init__()

    def _load_metadata(self) -> pd.DataFrame:
        "load the meta-data"

        raise Exception("Meta-Data table not populated yet")
        
        #xdir = os.path.dirname(__file__)
        #xpath = os.path.join(xdir, "meta_checks.json")
        #if not os.path.exists(xpath):
        #    raise Exception(f"Missing meta-data file: {xpath}")
        #return pd.read_json(xpath)


    def _load_content(self) -> pd.DataFrame:
        """Load the checks data from google sheet"""

        gs = WorksheetWrapper()
        url = gs.get_sheet_url("checks")

        df = gs.download_data(url)

        nrows = df.shape[0]

        df = gs.read_as_frame(df, "Checks!A2:S" + str(nrows), header_rows=1)

        # special case fixes:
        logger.info("special cases:")
        is_bad_pending = df["pending"].str.startswith("-")
        logger.info(f"  # rows with pending < 0: {is_bad_pending.shape[0]:,}")
        df.loc[is_bad_pending, "pending"] = "0"

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

    tab = TabChecks()
    tab.load()

    logger.info(f"checks\n{tab.df.to_json(orient='table', indent=2)}")



if __name__ == '__main__':
    main()
