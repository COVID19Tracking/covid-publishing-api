import collections
import csv
from io import StringIO

from flask import make_response

CSVColumn = collections.namedtuple('Column', 'label model_column')

def make_csv_response(columns, data):
    si = StringIO()
    writer = csv.writer(si)

    # write a header row
    writer.writerow([column.label for column in columns])

    # write data rows
    for datum in data:
        writer.writerow([datum.__getattribute__(column.model_column) for column in columns])
    output = make_response(si.getvalue())
    output.headers["Content-type"] = "text/csv"

    return output