import collections

from flask import render_template, Flask

ChangedRow = collections.namedtuple('ChangedRow', 'date state changed_values')
ChangedValue = collections.namedtuple('ChangedValue', 'field old new')


class EditDiff:
    """An object representing the set of changes made during an edit batch.

    Example:
        Sample EditDiff::
            changed_values = [ChangedValue(field="positive", old=123, new=456)]
            changed_rows = [ChangedRow(date="20200903", state="CA", changed_values=changed_values)]
            EditDiff(changed_rows, None)


    Attributes:
        changed_rows: a list of `ChangedRow` elements containing each edited row
        new_rows: a list of newly added rows, expressed as CoreData objects
    """

    def __init__(self, changed_rows, new_rows):
        self.changed_rows = changed_rows
        self.new_rows = new_rows

    def plain_text_format(self):
        """Return the diff in plain text format.

        The format is maintained in ``app/templates/editdiff.txt``"""
        return render_template("editdiff_plain.txt", changed_rows=self.changed_rows, new_rows=self.new_rows)
