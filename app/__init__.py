#/usr/bin/python
#-*- coding: utf-8 -*-
import flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.babel import Babel

app = flask.Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)
babel = Babel(app)


from app import views, models

if __name__ == '__main__':
	manager.run()
