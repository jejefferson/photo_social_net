#/usr/bin/python
#-*- coding: utf-8 -*-
from flask_wtf import Form
from flask_wtf.recaptcha import RecaptchaField
from wtforms import TextField, BooleanField, SubmitField, PasswordField, TextAreaField,\
	StringField, FileField, SelectField, DateField
from wtforms.validators import Required, Optional
from wtforms.widgets import TextArea
from wtforms.widgets.core import Select, HTMLString, html_params
from datetime import datetime
from flask_babel import gettext
from app import db, models
from wtforms.ext.sqlalchemy.fields import QuerySelectField
import os

list_countries=''
with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'countries.txt'), 'r') as file:
	list_countries = file.read().split('\n')

list_countries = [(q,w) for q,w in enumerate(list_countries)]

def Rquery():
	return models.User

class LoginForm(Form):
	text = TextField('text', validators = [Required()])
	message = TextField('message', validators = [Required()])
	remember_me = BooleanField('remember_me', default = False)
	show_logo = BooleanField('logo', default = False)
	
class RealLogin(Form):
	nickname = TextField('nick', validators = [Required()])
	password = PasswordField('password', validators = [Required()])
	email = TextField('email', validators = [Required()])
	remember_me = BooleanField('remember_me', default = True)
	#captcha = RecaptchaField()

class PostForm(Form):
	message = StringField('message', widget=TextArea(), validators = [Required()])
	show_logo = BooleanField('logo', default = False)

class SignForm(Form):
	nickname = TextField('nickname', validators = [Required()])
	password = PasswordField('password', validators = [Required()])
	remember_me = BooleanField('remember_me', default = False)

class SubmitForm(Form):
	submit = SubmitField('submit')

class ProfileChange(Form):
	user_pic = FileField('filename')
	user_gender = SelectField('gender', choices = [(0, u'male'), (1, u'female'), (2, u'trans'), (3, u'cyberpunk')], coerce=int, validators = [Optional()])
	user_location_country = SelectField('country', choices = list_countries, coerce = int)
	user_location_city = TextField('city')
	user_general_info = StringField('general_info', widget=TextArea())
	user_interests = StringField('interests', widget=TextArea())
	old_password = PasswordField('old_pass')
	new_password = PasswordField('new_pass')
	new_email = TextField('new_email')
	submit = SubmitField('submit')
	birth_date_day = SelectField('day', choices = [(q+1,w+1) for q,w in enumerate(range(31))], coerce=int)
	birth_date_month = SelectField('month', choices = [(q+1,w) for q,w in enumerate(['January','February', 'March',\
			'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'])], coerce=int)
	birth_date_year = SelectField('year', choices = [(int(datetime.now().strftime('%Y'))-q, int(datetime.now().strftime('%Y'))-w) for q,w in enumerate(range(100))], coerce=int)
	phone_number = TextField('phone')
	jid = TextField('jid')
	pgpkeyid = TextField('pgp')
	realname = TextField('realname')
	language = BooleanField('ru_lang')

class SendMessage(Form):
	message_body = StringField('message_body', widget=TextArea())
	message_dest = TextField('message_dest')
	id = TextField('id')
	submit = SubmitField(gettext('Send'))
	delete = SubmitField(gettext('delete'))
	read = SubmitField('read')
	message_file = FileField('file')

class SendComment(Form):
	comment_message_body = StringField('message_body', widget=TextArea())
	comment_message_dest = TextField('message_dest')
	comment_id = TextField('id')
	comment_submit = SubmitField(gettext('Send'))
	comment_delete = SubmitField(gettext('delete'))
	comment_read = SubmitField('read')
	comment_message_file = FileField('file')

class UploadForm(Form):
	link = TextField('link')

class PhotoGallery(Form):
	name = TextField('name')
	info = TextField('info')
	location = TextField('location')
	submit = SubmitField(gettext('add'))

class Gallery(Form):
	new_photo = FileField('photo')
	submit = SubmitField(gettext('add'))

class Photo(Form):
	comment = StringField('comment', widget=TextArea())
	submit = SubmitField(gettext('add'))

class SearchForm(Form):
	nickname = TextField('nickname')
	realname = TextField('realname')
	age = TextField('age')
	ageless = TextField('ageless')
	submit = SubmitField(gettext('to search'))
	clear = SubmitField(gettext('clear'))

class ImageSearchForm(Form):
	camera_model = SelectField('camera_model', default = 0)
	lens_model = SelectField('lens_model', default = 0)
	size = SelectField('size', choices = [(0, 'select'), (1, gettext('small')), (2,gettext('medium')), (3,gettext('big')), (4,gettext('old_full_shot')), (5, gettext('full_shot'))], default = 0, coerce = int)
	iso_from = TextField('iso_from')
	iso_to = TextField('iso_to')
	tags = TextField('tags')
	submit = SubmitField(gettext('to search'))
	clear = SubmitField(gettext('clear'))

class CreateGroup(Form):
	name = TextField('name')
	description = TextField('description')
	submit = SubmitField('create')

class GroupSendMessage(Form):
	message_body = StringField('message_body', widget=TextArea())
	message_dest = TextField('message_dest')
	id = TextField('id')
	submit = SubmitField(gettext('Send'))
	delete = SubmitField(gettext('delete'))
	read = SubmitField('read')
	message_file = FileField('file')
	owners_message = BooleanField('owner_message')

class GroupEdit(Form):
	description = StringField('description', widget=TextArea())
	pic = FileField('pic')
	submit = SubmitField('submit')
	tags = TextField('tags')
