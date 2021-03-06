"""empty message

Revision ID: 2b82dbdcfe12
Revises: 5300b45b99a0
Create Date: 2014-09-14 01:21:15.973684

"""

# revision identifiers, used by Alembic.
revision = '2b82dbdcfe12'
down_revision = '5300b45b99a0'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
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
    op.drop_constraint(u'entity', 'tag')
    op.drop_constraint(u'ix_tag_entity', 'tag')
    op.drop_index('ix_tag_entity', table_name='tag')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_index('ix_tag_entity', 'tag', ['entity'], unique=True)
    op.create_unique_constraint(u'ix_tag_entity', 'tag', ['entity'])
    op.create_unique_constraint(u'entity', 'tag', ['entity'])
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
    ### end Alembic commands ###
