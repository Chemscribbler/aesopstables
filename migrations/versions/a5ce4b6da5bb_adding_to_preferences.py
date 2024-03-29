"""adding to_preferences

Revision ID: a5ce4b6da5bb
Revises: e78123728e52
Create Date: 2023-08-25 18:12:01.466454

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a5ce4b6da5bb'
down_revision = 'e78123728e52'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('to_pref',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tid', sa.Integer(), nullable=False),
    sa.Column('allow_self_registration', sa.Boolean(), nullable=True),
    sa.Column('allow_self_results_report', sa.Boolean(), nullable=True),
    sa.Column('visible', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['tid'], ['tournament.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('to_pref')
    # ### end Alembic commands ###
