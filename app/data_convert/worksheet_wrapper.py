"""
Wrapper around GoogleSheets

Provides three main functions:
    1. assigns a symbolic name to a worksheet so the rest of the code doesn't depend 
    on a specific address.
    2.  

----

Credentials are stored in a json file which is encrypted with a preshared key.
The key is repo for our convenience so we do not have to share any secrets
to run the code.

This is NOT a security hole because (a) the worksheet is already public
and (b) the login account is readonly.  However, we may want to move to
a preshared-secret in the future -- Josh E.

"""

from typing import List, Dict
from loguru import logger
import pandas as pd
import numpy as np
import re

from google.oauth2 import service_account
from googleapiclient.discovery import build

from data_convert.encryption import access_encrypted_file, cleanup_encrypted_file

SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
KEY_PATH = "../../credentials-scanner.json"
KEY_PRESHARED_KEY = "covid"

class WorksheetWrapper():

    def __init__(self, debug = True):
        logger.info("load credentials")

        # pylint: disable=no-member
        tmp_path = access_encrypted_file(KEY_PRESHARED_KEY, KEY_PATH)
        try:
            self.creds = service_account.Credentials.from_service_account_file(
                tmp_path,
                scopes=SCOPES)
        finally:
            cleanup_encrypted_file(KEY_PATH)

        self.debug = debug
        if self.debug:
            logger.info(f"  email {self.creds.service_account_email}")
            logger.info(f"  project {self.creds.project_id}")
            logger.info(f"  scope {self.creds._scopes[0]}")
            logger.info("")
            logger.warning(" **** The private key for this identity is published in a public Github Repo")
            logger.warning(" **** DO NOT ALLOW ACCESS TO SENSITIVE/PRIVATE RESOURCES")
            logger.warning(" **** DO NOT ALLOW WRITE ACCESS ANYTHING")
            logger.info("")

        if self.debug: logger.info("connect")
        service = build('sheets', 'v4', credentials=self.creds)
        self.sheets = service.spreadsheets()


    def get_sheet_id_by_name(self, name: str) -> str:
        "get the id for a worksheet by symbolic name"
        items = {
            "dev": {
                "id": "1MvvbHfnjF67GnYUDJJiNYUmGco5KQ9PW0ZRnEP9ndlU",
                "url": "https://docs.google.com/spreadsheets/d/1MvvbHfnjF67GnYUDJJiNYUmGco5KQ9PW0ZRnEP9ndlU/edit#gid=1777138528"
            },
            "instructions": {
                "id": "1lGINxyLFuTcCJgVc4NrnAgbvvt09k3OiRizfwZPZItw",
                "url": "https://docs.google.com/document/d/1lGINxyLFuTcCJgVc4NrnAgbvvt09k3OiRizfwZPZItw/edit"
            },
            # don't know how to get to the underlying sheet so using the API - Josh
            #"published": {
            #    "id": "i7Tj0pvTf6XVHjDSMIKBdZHXiCGGdNC0ypEU9NbngS8mxea55JuCFuua1MUeOj5",
            #    "url": "https://docs.google.com/spreadsheets/u/2/d/e/2PACX-1vRwAqp96T9sYYq2-i7Tj0pvTf6XVHjDSMIKBdZHXiCGGdNC0ypEU9NbngS8mxea55JuCFuua1MUeOj5/pubhtml"
            #}
        }

        rec = items.get(name)
        if rec == None:
            raise Exception("Invalid name {name}, should be one of " + ", ".join([x for x in items]))
        return rec["id"]

    def get_grid_properties(self, sheet_id: str, tab_name: str) -> int:
        " get the properties of the tab "
        result = self.sheets.get(spreadsheetId=sheet_id, ranges=[tab_name], includeGridData=False).execute()
        return result["sheets"][0]["properties"]["gridProperties"]

#RL listFeedUrl = worksheets.get(x).getListFeedUrl();
#ListFeed feed = googleservice.getFeed(listFeedUrl, ListFeed.class);
#System.out.println("Number of filled rows"+feed_L.getEntries().size()+1);
#System.out.println("First Empty row"+feed_L.getEntries().size()+2)

    def read_values(self, sheet_id: str, cell_range: str) -> List[List]:
        """" 
        read a region of the sheet as a list of lists 
        
        returns data as a set of rows and cells.
        """

        if self.debug: logger.info(f"read {cell_range}")
        result = self.sheets.values().get(spreadsheetId=sheet_id, range=cell_range).execute()
        #if self.debug: logger.info(f"  {result}")

        values = result.get('values', [])
        return values



    def read_as_list(self, sheet_id: str, cell_range: str, ignore_blank_cells=False, single_row=False) -> List:
        """
        read a region of a sheet as a simple list or a list of list
        
        has an option to ignore blank cells
        has an option to return a single row
        """
        values = self.read_values(sheet_id, cell_range)
        if not ignore_blank_cells: return values
        
        result = []
        for row in values:
            result.append([x for x in row if x != ""])
        
        if single_row: result = result[0]
        return result

    def read_as_frame(self, sheet_id: str, cell_range: str, header_rows = 1) -> pd.DataFrame:
        """
        read a region of a sheet as a data frame
        
        first row(s) are used as the column names
        if there are more than one header row, the rows are combined to form the name

        returns a data frame
        """

        values = self.read_values(sheet_id, cell_range)

        header = values[0]
        if header_rows == 2:
            sub_header = values[1]
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

        n_cols = len(header)

        data = [[] for n in header]
        for r in values[header_rows:]:
            n_vals = len(r)
            if n_vals == 0: continue
            if n_vals < n_cols:
                #logger.warning(f"fewer columns than expected ({n_cols})")
                #logger.warning(f"  {r}")
                pass
            for i in range(n_vals):
                data[i].append(r[i])
            for i in range(n_vals, n_cols):
                data[i].append('')

        xdict = {}
        for n, vals in zip(header, data): xdict[n] = vals
        return pd.DataFrame(xdict)

