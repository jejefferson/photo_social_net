"""empty message

Revision ID: 3992f3c36823
Revises: 10c8a49cf5f
Create Date: 2014-08-09 22:05:32.704897

"""

# revision identifiers, used by Alembic.
revision = '3992f3c36823'
down_revision = '10c8a49cf5f'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('right',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('author', sa.String(length=64), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('body', sa.String(length=2048), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('left',
    sa.Column('file_id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=True),
    sa.Column('upload_data', sa.DateTime(), nullable=True),
    sa.Column('file_author', sa.String(length=64), nullable=True),
    sa.ForeignKeyConstraint(['file_author'], ['user.nickname'], ),
    sa.PrimaryKeyConstraint('file_id'),
    sa.UniqueConstraint('filename')
    )
    op.create_table('comments',
    sa.Column('left_id', sa.Integer(), nullable=True),
    sa.Column('right_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['left_id'], ['left.file_id'], ),
    sa.ForeignKeyConstraint(['right_id'], ['right.id'], )
    )
    op.drop_table('uploaded_file')
    op.drop_table('comment')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('comment',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('author', mysql.VARCHAR(collation=u'utf8_unicode_ci', length=255), nullable=True),
    sa.Column('date', mysql.DATETIME(), nullable=True),
    sa.Column('body', mysql.VARCHAR(collation=u'utf8_unicode_ci', length=2048), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate=u'utf8_unicode_ci',
    mysql_default_charset=u'utf8',
    mysql_engine=u'InnoDB'
    )
    op.create_table('uploaded_file',
    sa.Column('file_id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('filename', mysql.VARCHAR(collation=u'utf8_unicode_ci', length=255), nullable=True),
    sa.Column('upload_data', mysql.DATETIME(), nullable=True),
    sa.Column('file_author', mysql.VARCHAR(collation=u'utf8_unicode_ci', length=64), nullable=True),
    sa.ForeignKeyConstraint(['file_author'], [u'user.nickname'], name=u'uploaded_file_ibfk_1'),
    sa.PrimaryKeyConstraint('file_id'),
    mysql_collate=u'utf8_unicode_ci',
    mysql_default_charset=u'utf8',
    mysql_engine=u'InnoDB'
    )
    op.drop_table('comments')
    op.drop_table('left')
    op.drop_table('right')
    ### end Alembic commands ###
