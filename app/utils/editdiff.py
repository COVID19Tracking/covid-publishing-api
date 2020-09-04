import collections

from flask import render_template, Flask

ChangedValue = collections.namedtuple('ChangedValue', 'field old new')


class ChangedRow:
    def __init__(self, date, state, changed_values):
        ''' Changed values -- ChangedValue type'''
        self.date = date
        self.state = state
        self.changed_values = changed_values

    @property
    def changed_fields(self):
        return [c.field for c in self.changed_values]

    def __str__(self):
        return "ChangedRow({date}, {state}, {changed_values})".format(**self.__dict__)

    def __repr__(self):
        return self.__str__()


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

    @property
    def changed_fields(self):
        res = set()
        for row in self.changed_rows:
            res.update(row.changed_fields)

        return list(res)

    @property
    def changed_dates_str(self):
        '''Which dates changed in this diff'''
        if self.is_empty():
            return ""

        changed_dates = [c.date for c in self.changed_rows] + [c.date for c in self.new_rows]
        changed_dates = sorted(changed_dates)
        start = changed_dates[0].strftime('%-m/%-d/%y')
        end = changed_dates[-1].strftime('%-m/%-d/%y')
        changed_dates_str = start if start == end else '%s - %s' % (start, end)
        return changed_dates_str

    def size(self):
        # maybe implement it with len(diff)?
        res = len(self.changed_rows) if self.changed_rows else 0
        res += len(self.new_rows) if self.new_rows else 0
        return res

    def is_empty(self):
        return not self.changed_rows and not self.new_rows
