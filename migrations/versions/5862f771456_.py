"""empty message

Revision ID: 5862f771456
Revises: e7f56cc1511
Create Date: 2014-09-11 18:30:35.615947

"""

# revision identifiers, used by Alembic.
revision = '5862f771456'
down_revision = 'e7f56cc1511'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('message', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.alter_column('message', 'del_from_author',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    op.alter_column('message', 'del_from_dest',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    op.alter_column('message', 'is_read',
               existing_type=mysql.TINYINT(display_width=1),
               type_=sa.Boolean(),
               existing_nullable=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('message', 'is_read',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('message', 'del_from_dest',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.alter_column('message', 'del_from_author',
               existing_type=sa.Boolean(),
               type_=mysql.TINYINT(display_width=1),
               existing_nullable=True)
    op.drop_column('message', 'parent_id')
    ### end Alembic commands ###
