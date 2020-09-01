import collections
import csv
from io import StringIO

from flask import make_response

CSVColumn = collections.namedtuple('Column', 'label model_column')
"""Represents the recipe to generate a column of CSV output data. 

This maps a model column name to a CSV column name. An ordered list of CSVColumns can be passed to `make_csv_response`
to generate CSV output
Example: ``CSVColumn(label="State", model_column="state")``
"""


def make_csv_response(columns, data):
    """Generate a Flask response containing CSV data from `data` using the column definitions in ``columns``

    Outputs a header row, containing each column identified by the column's label in the order provided, followed by
    one line for each ``data`` row.

    Args:
        columns: A list of `CSVColumn` definitions. The output will contain each column in the given order
        data: SQLAlchemy query results to be output in CSV format

    Returns: Flask response in ``text/csv`` format
    """
    si = StringIO()
    writer = csv.writer(si)

    # write a header row
    writer.writerow([column.label for column in columns])

    # write data rows
    for datum in data:
        writer.writerow([datum.get(column.model_column) for column in columns])
    output = make_response(si.getvalue())
    output.headers["Content-type"] = "text/csv"

    return output
