"""empty message

Revision ID: 0c6db53f2db2
Revises: 62a65242ccf3
Create Date: 2020-06-26 17:55:26.309606

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0c6db53f2db2'
down_revision = '62a65242ccf3'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('coreData', 'pcrNegativeTests', new_column_name='negativeTestsViral')
    op.alter_column('coreData', 'pcrPositiveTests', new_column_name='positiveTestsViral')
    op.alter_column('coreData', 'pcrTotalTests', new_column_name='totalTestsViral')
    op.alter_column('coreData', 'pcrPositiveCases', new_column_name='positiveCasesViral')


def downgrade():
    op.alter_column('coreData', 'negativeTestsViral', new_column_name='pcrNegativeTests')
    op.alter_column('coreData', 'positiveTestsViral', new_column_name='pcrPositiveTests')
    op.alter_column('coreData', 'totalTestsViral', new_column_name='pcrTotalTests')
    op.alter_column('coreData', 'positiveCasesViral', new_column_name='pcrPositiveCases')
    
