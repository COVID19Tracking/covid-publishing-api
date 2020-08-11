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
    op.alter_column('coreData', 'totalTestsPeople', new_column_name='totalTestsPeopleViral')
    op.alter_column('coreData', 'totalAntibodyTests', new_column_name='totalTestsAntibody')
    op.alter_column('coreData', 'positiveAntibodyTests', new_column_name='positiveTestsAntibody')
    op.alter_column('coreData', 'negativeAntibodyTests', new_column_name='negativeTestsAntibody')
    op.alter_column('coreData', 'totalAntibodyTestsPeople', new_column_name='totalTestsPeopleAntibody')
    op.alter_column('coreData', 'positiveAntibodyTestsPeople', new_column_name='positiveTestsPeopleAntibody')
    op.alter_column('coreData', 'negativeAntibodyTestsPeople', new_column_name='negativeTestsPeopleAntibody')
    op.alter_column('coreData', 'totalAntigenTestsPeople', new_column_name='totalTestsPeopleAntigen')
    op.alter_column('coreData', 'positiveAntigenTestsPeople', new_column_name='positiveTestsPeopleAntigen')
    op.alter_column('coreData', 'totalAntigenTests', new_column_name='totalTestsAntigen')
    op.alter_column('coreData', 'positiveAntigenTests', new_column_name='positiveTestsAntigen')


def downgrade():
    op.alter_column('coreData', 'totalTestsPeopleViral', new_column_name='totalTestsPeople')
    op.alter_column('coreData', 'totalTestsAntibody', new_column_name='totalAntibodyTests')
    op.alter_column('coreData', 'positiveTestsAntibody', new_column_name='positiveAntibodyTests')
    op.alter_column('coreData', 'negativeTestsAntibody', new_column_name='negativeAntibodyTests')
    op.alter_column('coreData', 'totalTestsPeopleAntibody', new_column_name='totalAntibodyTestsPeople')
    op.alter_column('coreData', 'positiveTestsPeopleAntibody', new_column_name='positiveAntibodyTestsPeople')
    op.alter_column('coreData', 'negativeTestsPeopleAntibody', new_column_name='negativeAntibodyTestsPeople')
    op.alter_column('coreData', 'totalTestsPeopleAntigen', new_column_name='totalAntigenTestsPeople')
    op.alter_column('coreData', 'positiveTestsPeopleAntigen', new_column_name='positiveAntigenTestsPeople')
    op.alter_column('coreData', 'totalTestsAntigen', new_column_name='totalAntigenTests')
    op.alter_column('coreData', 'positiveTestsAntigen', new_column_name='positiveAntigenTests')
