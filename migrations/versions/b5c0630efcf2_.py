"""empty message

Revision ID: b5c0630efcf2
Revises: 7a2068644cd6
Create Date: 2020-08-11 12:20:39.363464

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b5c0630efcf2'
down_revision = '7a2068644cd6'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('coreData', 'totalTestsPeople', nullable=False, new_column_name='totalTestsPeopleViral')
    op.alter_column('coreData', 'totalAntibodyTests', nullable=False, new_column_name='totalTestsAntibody')
    op.alter_column('coreData', 'positiveAntibodyTests', nullable=False, new_column_name='positiveTestsAntibody')
    op.alter_column('coreData', 'negativeAntibodyTests', nullable=False, new_column_name='negativeTestsAntibody')
    op.alter_column('coreData', 'totalAntibodyTestsPeople', nullable=False, new_column_name='totalTestsPeopleAntibody')
    op.alter_column('coreData', 'positiveAntibodyTestsPeople', nullable=False, new_column_name='positiveTestsPeopleAntibody')
    op.alter_column('coreData', 'negativeAntibodyTestsPeople', nullable=False, new_column_name='negativeTestsPeopleAntibody')
    op.alter_column('coreData', 'totalAntigenTestsPeople', nullable=False, new_column_name='totalTestsPeopleAntigen')
    op.alter_column('coreData', 'positiveAntigenTestsPeople', nullable=False, new_column_name='positiveTestsPeopleAntigen')
    op.alter_column('coreData', 'totalAntigenTests', nullable=False, new_column_name='totalTestsAntigen')
    op.alter_column('coreData', 'positiveAntigenTests', nullable=False, new_column_name='positiveTestsAntigen')


def downgrade():
    op.alter_column('coreData', 'totalTestsPeopleViral', nullable=False, new_column_name='totalTestsPeople')
    op.alter_column('coreData', 'totalTestsAntibody', nullable=False, new_column_name='totalAntibodyTests')
    op.alter_column('coreData', 'positiveTestsAntibody', nullable=False, new_column_name='positiveAntibodyTests')
    op.alter_column('coreData', 'negativeTestsAntibody', nullable=False, new_column_name='negativeAntibodyTests')
    op.alter_column('coreData', 'totalTestsPeopleAntibody', nullable=False, new_column_name='totalAntibodyTestsPeople')
    op.alter_column('coreData', 'positiveTestsPeopleAntibody', nullable=False, new_column_name='positiveAntibodyTestsPeople')
    op.alter_column('coreData', 'negativeTestsPeopleAntibody', nullable=False, new_column_name='negativeAntibodyTestsPeople')
    op.alter_column('coreData', 'totalTestsPeopleAntigen', nullable=False, new_column_name='totalAntigenTestsPeople')
    op.alter_column('coreData', 'positiveTestsPeopleAntigen', nullable=False, new_column_name='positiveAntigenTestsPeople')
    op.alter_column('coreData', 'totalTestsAntigen', nullable=False, new_column_name='totalAntigenTests')
    op.alter_column('coreData', 'positiveTestsAntigen', nullable=False, new_column_name='positiveAntigenTests')
