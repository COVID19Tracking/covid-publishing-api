from data_convert.worksheet_wrapper import WorksheetWrapper
import pandas as pd


def test_working():

    ws = WorksheetWrapper()

    # get the information about the working sheet
    xid= ws.get_sheet_id_by_name("dev")

    props = ws.get_grid_properties(xid, "Worksheet 2")
    print(props)
    nrows = props["rowCount"]
    ncols = props["columnCount"]

    # this values will change if they change the worksheet
    assert(nrows == 60)
    assert(ncols == 78)

