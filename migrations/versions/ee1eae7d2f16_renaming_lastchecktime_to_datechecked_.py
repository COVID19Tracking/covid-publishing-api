"""Renaming lastCheckTime to dateChecked for public API consistency

Revision ID: ee1eae7d2f16
Revises: da977436076c
Create Date: 2020-05-19 18:22:58.099785

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ee1eae7d2f16'
down_revision = 'da977436076c'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('coreData', 'lastCheckTime', nullable=False, new_column_name='dateChecked')

def downgrade():
     op.alter_column('coreData', 'dateChecked', nullable=False, new_column_name='lastCheckTime')
