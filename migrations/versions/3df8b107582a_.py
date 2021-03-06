"""empty message

Revision ID: 3df8b107582a
Revises: f461bfac963
Create Date: 2014-08-09 22:42:56.186560

"""

# revision identifiers, used by Alembic.
revision = '3df8b107582a'
down_revision = 'f461bfac963'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('gallery',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('author', sa.String(length=255), nullable=True),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('info', sa.String(length=1024), nullable=True),
    sa.Column('upload_date', sa.DateTime(), nullable=True),
    sa.Column('location', sa.String(length=255), nullable=True),
    sa.ForeignKeyConstraint(['author'], ['user.nickname'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('photos',
    sa.Column('gallery_id', sa.Integer(), nullable=True),
    sa.Column('left_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['gallery_id'], ['gallery.id'], ),
    sa.ForeignKeyConstraint(['left_id'], ['left.file_id'], )
    )
    op.drop_table('photo_gallery')
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('photo_gallery',
    sa.Column('id', mysql.INTEGER(display_width=11), nullable=False),
    sa.Column('author', mysql.VARCHAR(collation=u'utf8_unicode_ci', length=255), nullable=True),
    sa.Column('name', mysql.VARCHAR(collation=u'utf8_unicode_ci', length=255), nullable=True),
    sa.Column('info', mysql.VARCHAR(collation=u'utf8_unicode_ci', length=1024), nullable=True),
    sa.Column('upload_date', mysql.DATETIME(), nullable=True),
    sa.Column('location', mysql.VARCHAR(collation=u'utf8_unicode_ci', length=255), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    mysql_collate=u'utf8_unicode_ci',
    mysql_default_charset=u'utf8',
    mysql_engine=u'InnoDB'
    )
    op.drop_table('photos')
    op.drop_table('gallery')
    ### end Alembic commands ###
