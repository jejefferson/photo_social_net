"""empty message

Revision ID: 1a9d5f25a63e
Revises: 23385684b584
Create Date: 2014-09-12 21:51:31.735325

"""

# revision identifiers, used by Alembic.
revision = '1a9d5f25a63e'
down_revision = '23385684b584'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_index(op.f('ix_comments_left_id'), 'comments', ['left_id'], unique=False)
    op.create_index(op.f('ix_comments_right_id'), 'comments', ['right_id'], unique=False)
    op.create_index(op.f('ix_friends_friended_id'), 'friends', ['friended_id'], unique=False)
    op.create_index(op.f('ix_friends_friender_id'), 'friends', ['friender_id'], unique=False)
    op.create_index(op.f('ix_left_access'), 'left', ['access'], unique=False)
    op.create_index(op.f('ix_left_file_author'), 'left', ['file_author'], unique=False)
    op.create_index(op.f('ix_left_upload_data'), 'left', ['upload_data'], unique=False)
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
    op.create_index(op.f('ix_photos_gallery_id'), 'photos', ['gallery_id'], unique=False)
    op.create_index(op.f('ix_photos_left_id'), 'photos', ['left_id'], unique=False)
    op.create_index(op.f('ix_tags_left_id'), 'tags', ['left_id'], unique=False)
    op.create_index(op.f('ix_tags_message_id'), 'tags', ['message_id'], unique=False)
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_tags_message_id'), table_name='tags')
    op.drop_index(op.f('ix_tags_left_id'), table_name='tags')
    op.drop_index(op.f('ix_photos_left_id'), table_name='photos')
    op.drop_index(op.f('ix_photos_gallery_id'), table_name='photos')
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
    op.drop_index(op.f('ix_left_upload_data'), table_name='left')
    op.drop_index(op.f('ix_left_file_author'), table_name='left')
    op.drop_index(op.f('ix_left_access'), table_name='left')
    op.drop_index(op.f('ix_friends_friender_id'), table_name='friends')
    op.drop_index(op.f('ix_friends_friended_id'), table_name='friends')
    op.drop_index(op.f('ix_comments_right_id'), table_name='comments')
    op.drop_index(op.f('ix_comments_left_id'), table_name='comments')
    ### end Alembic commands ###
