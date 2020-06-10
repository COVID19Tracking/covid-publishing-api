"""empty message

Revision ID: bbf03457c455
Revises: fea4af6bf9ce
Create Date: 2020-06-02 20:03:31.707936

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bbf03457c455'
down_revision = 'fea4af6bf9ce'
branch_labels = None
depends_on = None


def upgrade():
    # add the column "date" to the primary key
    op.drop_constraint('coreData_pkey', 'coreData', type_='primary')
    op.create_primary_key(
            'coreData_pkey', 'coreData', ['state', 'batchId', 'date'])


def downgrade():
    # return to a primary key without "date"
    op.drop_constraint('coreData_pkey', 'coreData', type_='primary')
    op.create_primary_key('coreData_pkey', 'coreData', ['state', 'batchId'])
