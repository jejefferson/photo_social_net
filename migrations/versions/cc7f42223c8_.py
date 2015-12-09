"""empty message

Revision ID: cc7f42223c8
Revises: 48dd4abc2f44
Create Date: 2014-09-11 18:07:16.502254

"""

# revision identifiers, used by Alembic.
revision = 'cc7f42223c8'
down_revision = '48dd4abc2f44'

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
    op.alter_column('user', 'user_birthday',
               existing_type=mysql.VARCHAR(collation=u'utf8_unicode_ci', length=32),
               type_=sa.DateTime(),
               existing_nullable=True)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'user_birthday',
               existing_type=sa.DateTime(),
               type_=mysql.VARCHAR(collation=u'utf8_unicode_ci', length=32),
               existing_nullable=True)
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
