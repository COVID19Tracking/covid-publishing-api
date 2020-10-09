from datetime import datetime

import pytz

from app import db
from app.models.data import Batch, State, CoreData
from app.utils.editdiff import EditDiff, ChangedValue, ChangedRow


def test_editdiff(app):
    with app.app_context():
        changed_values = [ChangedValue(field="positive", old=123, new=456), ChangedValue(field="negative", old=555, new=666)]
        changed_rows = [ChangedRow(date="20200903", state="CA", changed_values=changed_values)]
        ed = EditDiff(changed_rows, None)
        output = ed.plain_text_format()

        assert "Rows edited: 1" in output
        assert "CA 20200903" in output
        assert "positive: 456 (was 123)" in output
        assert "New rows" not in output
        assert not output.startswith("\n")  # ensure no leading newlines

        nys = State(state='NY', totalTestResultsFieldDbColumn="posNeg")
        bat = Batch(batchNote='test', createdAt=datetime.now(),
                    isPublished=False, isRevision=False)
        db.session.add(bat)
        db.session.add(nys)
        db.session.flush()

        date1 = datetime(2020, 5, 4, 20, 3, tzinfo=pytz.UTC)
        core_data_row = CoreData(
            lastUpdateIsoUtc=date1.isoformat(), dateChecked=date1.isoformat(),
            date=date1, state='NY', batchId=bat.batchId,
            positive=20, negative=5)
        date2 = datetime(2020, 5, 5, 20, 3, tzinfo=pytz.UTC)
        core_data_row2 = CoreData(
            lastUpdateIsoUtc=date2.isoformat(), dateChecked=date2.isoformat(),
            date=date2, state='NY', batchId=bat.batchId,
            positive=25, negative=5)
        new_rows = [core_data_row, core_data_row2]

        ed = EditDiff(changed_rows, new_rows)
        output = ed.plain_text_format()
        assert "Rows edited: 1" in output
        assert "New rows: 2" in output
        assert f"NY {date1.strftime('%Y-%m-%d')}\nNY {date2.strftime('%Y-%m-%d')}" in output
