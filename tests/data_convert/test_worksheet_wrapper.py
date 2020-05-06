from data_convert.worksheet_wrapper import WorksheetWrapper
import pandas as pd


def test_column_names():

    ws = WorksheetWrapper()

    names = ws.generate_column_names(4)
    assert(names == ["A","B", "C", "D"])
    
    names = ws.generate_column_names(28)
    assert(names[-2] == "AA")
    assert(names[-1] == "AB")


def test_parse_names():

    ws = WorksheetWrapper()

    xstart, xstop = ws.parse_range("A1:D10")
    assert(xstart == ('A',0))
    assert(xstop == ('D',9))
    
    xstart, xstop = ws.parse_range("AA5:AZ100")
    assert(xstart == ('AA',4))
    assert(xstop == ('AZ',99))


def test_read_list():

    df = pd.DataFrame({"A": ["1", "A", "3", "4", "5"]})
    df["B"] = df["A"]
    df["C"] = df["A"]
    df["D"] = df["A"]
    
    df.iloc[1, 1] = ""
    df.iloc[1, 2] = "C"
    df.iloc[1, 3] = "D"

    print(f"input = \n{df}")
    ws = WorksheetWrapper()

    result = ws.read_as_list(df, "B2:C3")
    assert(result == [[ "", "C"], ["3", "3"]])
    result = ws.read_as_list(df, "B2:C3", ignore_blank_cells=True)
    assert(result == [[ "C"], ["3", "3"]])
    result = ws.read_as_list(df, "B2:D2", single_row=True)
    assert(result == [ "", "C", "D"])
    result = ws.read_as_list(df, "B2:D2", ignore_blank_cells=True, single_row=True)
    assert(result == [ "C", "D"])


def test_read_frame():
    df_raw = pd.DataFrame({
        "A": ["", "C1", "3", "4", "5"],
        "B": ["", "C2", "13", "14", "15"],
        "C": ["", "C3", "23", "24", "25"],
        })

    print(f"input = \n{df_raw}")
    ws = WorksheetWrapper()
    df = ws.read_as_frame(df_raw, "B2:C4")
    print(f"output = \n{df}")

    assert(df.shape == (2,2))
    assert(df.columns.tolist() == ["C2", "C3"])
    assert(df.C2.iloc[0] == "13")
    assert(df.C3.iloc[-1] == "24")


def test_working():

    ws = WorksheetWrapper()

    # get the information about the working sheet
    url = ws.get_sheet_url("working")
    df_raw = ws.download_data(url)

    # this values will change if they change the worksheet
    assert(df_raw.shape[0] == 58)
    assert(df_raw.shape[1] == 70)

    nrows = df_raw.shape[0]
    df = ws.read_as_frame(df_raw, "A2:S" + str(nrows+1))
    print(f"df=\n{df.head()}")
    assert(df.columns[0] == "State")
    assert(df.State[0] == "AK")

