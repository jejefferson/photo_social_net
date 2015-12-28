#/usr/bin/python
#-*- coding: utf-8 -*-

import os
from app import app
from app import db, models
from exceptions import *
import datetime
from sqlalchemy import desc, or_
from sqlalchemy.orm import eagerload, joinedload, subqueryload, aliased
from werkzeug.utils import secure_filename

try:
    import Image
except:
    from PIL import Image
from PIL.ExifTags import TAGS

def file_is_image(filename):
	return filename.rsplit('.', 1)[1].lower() in ['jpg', 'jpeg', 'png', 'gif', 'bmp']

def file_is_audio(filename):
	return filename.rsplit('.', 1)[1].lower() in ['mp3', 'ogg', 'wav']
	
def save_thumb(filename):
	im = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	im.thumbnail((400, 400), Image.ANTIALIAS)
	open(os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails/', filename)), 'a').close()
	im.save(os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails/', filename)),\
		'JPEG', quality=75)

def register_new_user(nickname, password, email, role=models.ROLE_USER, language='en'):
	if len(db.session.query(models.User.nickname).filter(models.User.nickname == nickname).all()):
		app.logger.info("ERROR! Nickname already registered!")
		raise AlreadyRegistered
	if email in [u.email for u in models.User.query.all()]: #todo: переписать
		app.logger.info("ERROR! Email already used!")
		raise EmailAlreadyUsed
	date = datetime.datetime.utcnow()
	pic = app.config['DEFAULT_USERPIC']
	db.session.add(models.User(nickname=nickname, password=password, email=email, role=role,\
		registration_data=date, language=language, user_pic=pic))
	db.session.commit()

def _get_exif(filename):
	img = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], filename))
	try:
		exif_info = img._getexif()
	except AttributeError:
		exif_info = None
	if exif_info:
		all_exif = { TAGS[k]: v for k, v in exif_info.items() if k in TAGS }
		exp = all_exif.get('ExposureTime')
		fnumber = None
		fnr = all_exif.get('FNumber')
		focallength = all_exif.get('FocalLength')
		if focallength and focallength[1] != 0:
			focallength = float(focallength[0])/float(focallength[1])
		if fnr and fnr[1] != 0:
			fnumber = float(fnr[0])/float(fnr[1])
		exposure_divident = None
		exposure_divisor = None
		if exp:
			exposure_divident = exp[0]
			exposure_divisor = exp[1]
		flash = all_exif.get('Flash')
		exif = models.Exif(width = all_exif.get('ExifImageWidth'),
			height = all_exif.get('ExifImageHeight'), iso = all_exif.get('ISOSpeedRatings'),
			model =  all_exif.get('Model'), lens_model = all_exif.get('LensModel'), date = all_exif.get('DateTime'),
			exposure_divident = exposure_divident, exposure_divisor = exposure_divisor, fnumber = fnumber,
			focallength = focallength, flash = flash)
	else: exif = None
	return exif

def get_user_by_nick(nickname):
	user = models.User.query.filter_by(nickname=nickname).first()
	return user

def _truncate_tags(message):
	if message:
		res = message.split(' ')
		tags = []
		for each in res:
				if each.startswith('#'):
						tags.append(each)
				else:
						break
		res = filter(lambda x: x not in tags, res)
		tags = map(lambda x: x.strip('#'), tags)
		return (tags, ' '.join(res))
	else:
		return None

def _add_all_attachments(message, uploaded_files, private = False):
	for message_file in uploaded_files:
		if not message_file.filename:
			continue
		if isinstance(message, models.PhotoGallery):
			if message_file.mimetype not in IMAGES:
				continue
				flash(gettext('You may download only images in gallery'))
		filename = os.path.basename(message_file.filename)
		filename = datetime.datetime.utcnow().strftime('%y.%m.%d_%H:%M:%S_') + filename
		access = 'private' if private else 'public'
		if not len(db.session.query(models.UploadedFile.filename).filter(models.UploadedFile.filename == filename).all()):
			app.logger.info(filename)
			message_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
			exif = None
			if file_is_image(filename):
				save_thumb(filename)
				exif = _get_exif(filename)
			if isinstance(message, models.Message):
				message = message.add_file(models.UploadedFile(file_author=message.msg_author, filename=filename,\
						access=access, exif=exif, mimetype=message_file.content_type,\
						upload_data=datetime.datetime.utcnow()))
			elif isinstance(message, models.PhotoGallery):
				message = message.add_photo(models.UploadedFile(file_author=session.get('nickname'), filename=filename,\
						access=access, exif=exif, mimetype=message_file.content_type,\
						upload_data=datetime.datetime.utcnow()))
	return message

def add_message(msg_author, msg_dest, msg_type, msg_body, uploaded_files=None, group_id=None):
	if msg_type == 'blog' and msg_body:
		tags, msg = _truncate_tags(msg_body)
	else:
		tags = None
		msg = msg_body
	#app.logger.info('dest is: %s' % msg_dest)
	if msg_type == 'private':
		if not len(msg_dest):
			flash(gettext('You need fill destination field'))
			return None
		if msg_dest == msg_author:
			flash(gettext('You can not send message to myself'))
			return None
		if not len(db.session.query(models.User.nickname).filter(models.User.nickname == msg_dest).all()):
			flash(gettext('No such username, you should specify a real user name'))
			return None
	if uploaded_files:
		uploaded_files = [filex for filex in uploaded_files if filex.filename]
	if not msg and not uploaded_files:
		flash(gettext('So where your message?'))
		return None
	message = models.Message(body=msg, msg_author=msg_author, msg_dest=msg_dest, msg_type=msg_type,\
				timestamp=datetime.datetime.utcnow(), del_from_author=False, del_from_dest=False, group_id=group_id)
	db.session.add(message)
	if uploaded_files:
		message = _add_all_attachments(message, uploaded_files)
	db.session.commit()
	if msg_type == 'blog' and tags:
		for tag in tags:
			q,w = message.add_tag(models.Tag(entity=tag))
			if q: db.session.add(w)
			else: db.session.execute(w)
	db.session.commit()
	return message
	
def get_last_chat_messages(count):
	messages = db.session.query(models.Message).filter(models.Message.msg_type == 'chat').\
		order_by(desc(models.Message.msg_id)).limit(count).all()
	messages.reverse()
	return messages

def update_message_attachments(message, files, access):
	message = _add_all_attachments(message, files, access)
	db.session.add(message)
	db.session.commit()
