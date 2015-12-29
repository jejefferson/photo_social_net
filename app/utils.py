#/usr/bin/python
#-*- coding: utf-8 -*-

import os
from app import app

try:
    import Image
except:
    from PIL import Image

IMAGES = ['image/png', 'image/jpeg', 'image/gif', 'image/bmp']

def humansize(nbytes):
	suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
	if nbytes == 0: return '0 B'
	i = 0
	while nbytes >= 1024 and i < len(suffixes)-1:
		nbytes /= 1024.
		i += 1
	f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
	return '%s %s' % (f, suffixes[i])

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

def truncate_tags(message):
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
