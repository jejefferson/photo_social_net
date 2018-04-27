#/usr/bin/python
#-*- coding: utf-8 -*-

import os
import logging

import flask
from flask_sqlalchemy import SQLAlchemy
from flask_babel import Babel

app = flask.Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
babel = Babel(app)


def create_dir_safe(pathdir):
    if not os.path.exists(pathdir):
        os.makedirs(pathdir)


for dirname in ('PATH_LOG_FILE', 'UPLOAD_FOLDER', 'UPLOAD_THUMBS_FOLDER'):
    create_dir_safe(os.path.dirname(app.config.get(dirname)))

# Logging for docker stream
# For file logging use for example: logging.handlers.RotatingFileHandler(app.config.get('PATH_LOG_FILE'), maxBytes=app.config.get('LOG_FILE_SIZE'), backupCount=1)

handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)


from app import views, models

if __name__ == '__main__':
	manager.run()
