#/usr/bin/python
#-*- coding: utf-8 -*-
from app import db

ROLE_USER = 0
ROLE_ADMIN = 1

friends = db.Table('friends',
    db.Column('friender_id', db.Integer, db.ForeignKey('user.id'), index = True),
    db.Column('friended_id', db.Integer, db.ForeignKey('user.id'), index = True)
)

groups = db.Table('group_admin',
	db.Column('participant_id', db.Integer, db.ForeignKey('user.id'), index = True),
	db.Column('group_id', db.Integer, db.ForeignKey('group.id'), index = True)
)

comments = db.Table('comments',
    db.Column('left_id', db.Integer, db.ForeignKey('left.file_id'), index = True),
    db.Column('right_id', db.Integer, db.ForeignKey('right.id'), index = True)
)

photos = db.Table('photos',
	db.Column('gallery_id', db.Integer, db.ForeignKey('gallery.id'), index = True),
	db.Column('left_id', db.Integer, db.ForeignKey('left.file_id'), index = True)
)

tags = db.Table('tags',
	db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), index = True),
	db.Column('left_id', db.Integer, db.ForeignKey('left.file_id'), index = True),
	db.Column('message_id', db.Integer, db.ForeignKey('message.msg_id'), index = True),
	db.Column('group_id', db.Integer, db.ForeignKey('group.id'), index=True)
)
	

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(64), index = True, unique = True)
    password = db.Column(db.String(64))
    email = db.Column(db.String(120), index = True, unique = True)
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    registration_data = db.Column(db.DateTime)
    user_pic = db.Column(db.String(255))
    user_gender = db.Column(db.Enum(u'male', u'female', u'trans', u'cyberpunk'))
    user_location_country = db.Column(db.String(64))
    user_location_city = db.Column(db.String(64))
    user_general_info = db.Column(db.String(1024))
    user_interests = db.Column(db.String(1024))
    user_birthday = db.Column(db.DateTime)
    phone_number = db.Column(db.String(32))
    jid = db.Column(db.String(32))
    pgpkeyid = db.Column(db.String(6000))
    realname = db.Column(db.String(64), index = True)
    language = db.Column(db.String(8))
    last_online_time = db.Column(db.DateTime)
    messages = db.relationship('Message', backref = 'user', lazy = 'dynamic')
    uploaded_files = db.relationship('UploadedFile', backref = 'user', lazy = 'dynamic')
    friended = db.relationship('User', secondary = friends,\
			primaryjoin = (friends.c.friender_id == id),\
			secondaryjoin = (friends.c.friended_id == id),\
			backref = db.backref('friends', lazy = 'dynamic'),\
			lazy = 'dynamic')
    galleries = db.relationship('PhotoGallery', backref = 'user', lazy = 'dynamic')
    def to_friend(self, user):
		if not self.is_friended(user):
			self.friended.append(user)
			return self
	
    def to_ufriend(self, user):
		if self.is_friended(user):
			self.friended.remove(user)
			return self
    def is_friend(self, user):
        return self.friended.filter_by(nickname = user.nickname).count() > 0
			
    def is_friended(self, user):
		return self.friended.filter(friends.c.friended_id == user.id).count() > 0
	
    def __repr__(self):
        return '<User %r>' % (self.nickname)

class Message(db.Model):
	msg_id = db.Column(db.Integer, primary_key = True)
	parent_id = db.Column(db.Integer, db.ForeignKey('message.msg_id'), index = True)
	body = db.Column(db.String(9600))
	timestamp = db.Column(db.DateTime, index = True)
	group_id = db.Column(db.Integer, db.ForeignKey('group.id'), index = True)
	msg_author = db.Column(db.String(64), db.ForeignKey('user.nickname'), index = True)
	msg_dest = db.Column(db.String(64), index = True)
	msg_type = db.Column(db.Enum(u'chat', u'blog', u'private', u'comment', u'group'), index = True)
	reply_to = db.Column(db.Integer)
	del_from_author = db.Column(db.Boolean, default = False)
	del_from_dest = db.Column(db.Boolean, default = False)
	is_read = db.Column(db.Boolean, default = False, index = True)
	attachment = db.Column(db.String(255)) # legacy
	comments = db.relationship('Message', backref=db.backref('parent', remote_side=[msg_id]), lazy = 'subquery')
	attachments = db.relationship('UploadedFile', backref = 'message', lazy = 'dynamic')
	attachments_subqueryload = db.relationship('UploadedFile', backref = 'Message', lazy = 'subquery')
	tags = db.relationship('Tag', backref = 'message', secondary = tags, lazy = 'subquery')
	
	def add_comment(self, comment):
		self.comments.append(comment)
		return self
	
	def remove_comment(self, comment):
		self.comments.remove(comment)
		return self
	
	def add_file(self, file):
		self.attachments.append(file)
		return self
	
	def add_tag(self, tag):
		exist = Tag.query.filter_by(entity=tag.entity).first()
		if exist:
			self.tags.append(exist)
			return True, self
		self.tags.append(tag)
		return True, self
			
	def remove_tag(self, tag):
		self.tags.remove(tag)
		print tag.photo, tag.message
		if not tag.photo and not tag.message and not tag.group:
			db.session.delete(tag)
			db.session.commit()
		return True, self
			
	def __repr__(self):
		return '<Post %r>' % (self.body)

class UploadedFile(db.Model):
	__tablename__ = 'left'
	file_id = db.Column(db.Integer, primary_key = True)
	filename = db.Column(db.String(255), unique = True)
	upload_data = db.Column(db.DateTime, index = True)
	file_author = db.Column(db.String(64), db.ForeignKey('user.nickname'), index = True)
	msg_id = db.Column(db.Integer, db.ForeignKey('message.msg_id'), index = True)
	name = db.Column(db.String(255))
	access = db.Column(db.Enum(u'file_exchange', u'public', u'private', u'reserve'), index = True)
	mimetype = db.Column(db.String(128))
	comments = db.relationship('Comment', secondary=comments, backref = 'file', lazy = 'dynamic', cascade = 'all,delete')
	exif = db.relationship('Exif', uselist = False, backref = 'photo')
	tags = db.relationship('Tag', backref = 'photo', secondary = tags, lazy = 'dynamic')
	
	def add_comment(self, comment):
		self.comments.append(comment)
		return self
		
	def add_tag(self, tag):
		exist = Tag.query.filter_by(entity=tag.entity).first()
		if exist:
			self.tags.append(exist)
			return True, self
		self.tags.append(tag)
		return True, self
			
	def remove_tag(self, tag):
		self.tags.remove(tag)
		if not tag.photo and not tag.message and not tag.group:
			db.session.delete(tag)
			db.session.commit()
		return True, self

class PhotoGallery(db.Model):
	__tablename__ = 'gallery'
	id = db.Column(db.Integer, primary_key = True)
	author = db.Column(db.String(255), db.ForeignKey('user.nickname'))
	name = db.Column(db.String(255))
	info = db.Column(db.String(1024))
	upload_date = db.Column(db.DateTime)
	photos = db.relationship('UploadedFile', secondary=photos,backref = 'photogallery', lazy = 'dynamic')
	location = db.Column(db.String(255))
	
	def add_photo(self, uploaded_file):
		self.photos.append(uploaded_file)
		return self

class Comment(db.Model):
	__tablename__ = 'right'
	id = db.Column(db.Integer, primary_key = True)
	author = db.Column(db.String(64), index = True)
	date = db.Column(db.DateTime)
	body = db.Column(db.String(2048))

class Exif(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	photo_id = db.Column(db.Integer, db.ForeignKey('left.file_id'), index = True)
	width = db.Column(db.Integer)
	height = db.Column(db.Integer)
	iso = db.Column(db.Integer)
	model = db.Column(db.String(255), index = True)
	lens_model = db.Column(db.String(255), index = True)
	date = db.Column(db.String(32))
	exposure_divident = db.Column(db.SmallInteger)
	exposure_divisor = db.Column(db.SmallInteger)
	fnumber = db.Column(db.Float)
	focallength = db.Column(db.Float)
	flash = db.Column(db.SmallInteger)

class Tag(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	entity = db.Column(db.String(32))

class Group(db.Model):
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(255))
	description = db.Column(db.String(2048))
	pic = db.Column(db.String(255))
	owner = db.Column(db.String(64), index = True)
	date_create = db.Column(db.DateTime)
	messages = db.relationship('Message', backref = 'group', lazy = 'dynamic')
	tags = db.relationship('Tag', backref = 'group', secondary = tags, lazy = 'subquery')
	participants = db.relationship('User', secondary = groups, backref = 'groups', lazy = 'dynamic')
	
	def subscribe(self, user):
		if user not in self.participants:
			self.participants.append(user)
			return self
		else:
			return None
	
	def unsubscribe(self, user):
		if user in self.participants:
			self.participants.remove(user)
			return self
		else:
			return None
	
	def subscribe_tag(self, tag):
		exist = Tag.query.filter_by(entity=tag.entity).first()
		if exist:
			self.tags.append(exist)
			return self
		self.tags.append(tag)
		return self
			
	def unsubscribe_tag(self, tag):
		tag = Tag.query.filter_by(entity=tag).first()
		self.tags.remove(tag)
		if not tag.photo and not tag.message and not tag.group:
			db.session.delete(tag)
			db.session.commit()
		return self
