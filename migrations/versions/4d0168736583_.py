"""empty message

Revision ID: 4d0168736583
Revises: 3d404fa73580
Create Date: 2014-10-30 23:46:04.644531

"""

# revision identifiers, used by Alembic.
revision = '4d0168736583'
down_revision = '3d404fa73580'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('message', sa.Column('group_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_message_group_id'), 'message', ['group_id'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_message_group_id'), table_name='message')
    op.drop_column('message', 'group_id')
    ### end Alembic commands ###
