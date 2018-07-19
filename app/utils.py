# /usr/bin/python
# -*- coding: utf-8 -*-

import os
import re

from typing import (
    List,
    Tuple,
)

try:
    import Image
except:
    from PIL import Image

from app import app


IMAGES = ['image/png', 'image/jpeg', 'image/gif', 'image/bmp']


def humansize(nbytes):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    if nbytes == 0: return '0 B'
    i = 0
    while nbytes >= 1024 and i < len(suffixes) - 1:
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
    im.save(
        os.path.abspath(
            os.path.join(
                app.config['UPLOAD_FOLDER'],
                'thumbnails/',
                filename,
            )
        ),
        'PNG',  # jpeg is not possible due to having rgba in some cases
        quality=75,
    )


def extract_tags(message):
    if message:
        message = message.strip()
        if not message.startswith('#'):
            return [], message
        words = message.split(' ')
        index = 0
        for word in words:
            if not word.startswith('#'):
                index = message.find(word)
                break  # capture only first entries
        tags = filter(None, message[:index-1].split('#'))
        text = message[index:]
        return tags, text
