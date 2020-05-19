"""rename date to dataDate

Revision ID: da977436076c
Revises: 0d412b939e30
Create Date: 2020-05-19 13:55:05.472789

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da977436076c'
down_revision = '0d412b939e30'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('coreData', 'date', nullable=False, new_column_name='dataDate')

def downgrade():
    op.alter_column('coreData', 'dataDate', nullable=False, new_column_name='date')
