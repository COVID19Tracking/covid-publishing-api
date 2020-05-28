"""Renaming dataDate to date

Revision ID: fea4af6bf9ce
Revises: 01f76bf60f51
Create Date: 2020-05-27 22:51:45.711845

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fea4af6bf9ce'
down_revision = '01f76bf60f51'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('coreData', 'dataDate', nullable=False, new_column_name='date')


def downgrade():
    op.alter_column('coreData', 'date', nullable=False, new_column_name='dataDate')
