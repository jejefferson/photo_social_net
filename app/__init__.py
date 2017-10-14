#/usr/bin/python
#-*- coding: utf-8 -*-

import os
import logging
from logging.handlers import RotatingFileHandler

import flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.babel import Babel

app = flask.Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
babel = Babel(app)


def create_dir_safe(pathdir):
    if not os.path.exists(pathdir):
        os.makedirs(pathdir)


for dirname in ('PATH_LOG_FILE', 'UPLOAD_FOLDER', 'UPLOAD_THUMBS_FOLDER'):
    create_dir_safe(os.path.dirname(app.config.get(dirname)))

handler = RotatingFileHandler(app.config.get('PATH_LOG_FILE'), maxBytes=app.config.get('LOG_FILE_SIZE'), backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)


from app import views, models

if __name__ == '__main__':
	manager.run()
