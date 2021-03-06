"""empty message

Revision ID: 59b009e948f9
Revises: 1eaee12eb99a
Create Date: 2014-09-06 01:56:58.024483

"""

# revision identifiers, used by Alembic.
revision = '59b009e948f9'
down_revision = '1eaee12eb99a'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('left', sa.Column('access', sa.Enum(u'file_exchange', u'public', u'private', u'reserve'), nullable=True))
    op.drop_column('left', 'acceess')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('left', sa.Column('acceess', mysql.ENUM(u'file_exchange', u'public', u'private', u'reserve'), nullable=True))
    op.drop_column('left', 'access')
    ### end Alembic commands ###
