# -*- coding: utf-8 -*-
from app import app
from app import core_api
from app.exceptions import *
import flask
from flask import render_template, flash, redirect, session, request, url_for, send_from_directory, \
    make_response, get_flashed_messages, g
from app.retrieve2 import CacheRData
from app.forms import LoginForm, RealLogin, PostForm, SignForm, SubmitForm, ProfileChange, SendMessage, UploadForm, \
    PhotoGallery, Gallery, Photo, SearchForm, ImageSearchForm, SendComment, CreateGroup, GroupSendMessage, \
    GroupEdit, list_countries  # todo replace list_countries
from app import models, db, babel
import datetime
from sqlalchemy import desc, or_
from sqlalchemy.orm import eagerload, joinedload, subqueryload, aliased
from werkzeug.utils import secure_filename
import os
from pytz import timezone
import itsdangerous
from flask.ext.babel import gettext, ngettext
import jinja2

try:
    import Image
except:
    from PIL import Image
from PIL.ExifTags import TAGS
from werkzeug import SharedDataMiddleware
from werkzeug.routing import IntegerConverter as BaseIntConverter
import wand.image
from dateutil.relativedelta import relativedelta
from flask import jsonify
import urllib
from functools import wraps
import sys
from app import utils

try:
    from uwsgidecorators import timer


    @timer(app.config.get('TIMEOUT_SOCIAL') * 60)
    def dump_last_online_date(signum):
        recent_online_users = [usr for usr, lasttime in ONLINE_SOCIAL_TABLE.items() if \
                               lasttime + datetime.timedelta(minutes=app.config['TIMEOUT_SOCIAL'],
                                                             seconds=10) < datetime.datetime.utcnow()]
        if recent_online_users:
            for user in recent_online_users:
                app.logger.info(
                    'I sew recent online user: %s at %s' % (user, ONLINE_SOCIAL_TABLE[user].strftime('%H:%M:%S')))
                dbuser = models.User.query.filter_by(nickname=user).first()
                dbuser.last_online_time = ONLINE_SOCIAL_TABLE[user]
                db.session.add(dbuser)
                del ONLINE_SOCIAL_TABLE[user]
            db.session.commit()
except ImportError:
    app.logger.error('Application was run out of the UWSGI, so you cant dump last online for users!')


def redirect_url(default='profile'):
    return request.args.get('next') or \
           request.referrer or \
           url_for(default)


def timezoned(timestamp):
    return timezone(app.config['TZ']).fromutc(timestamp).strftime("%y-%m-%d %H:%M:%S")


def escape_slashes(url):
    return urllib.quote(url, '')


def interpret_flash(flash):
    flash = {0: 'No', 1: 'Yes', 5: 'Yes', 7: 'Yes', 8: 'No', 9: 'Yes', 13: 'Yes',
             15: 'Yes', 16: 'No', 20: 'No', 24: 'No', 25: 'Yes', 29: 'Yes', 31: 'Yes',
             32: 'No', 48: 'No', 65: 'Yes', 69: 'Yes', 71: 'Yes', 73: 'Yes', 77: 'Yes',
             79: 'Yes', 80: 'No', 88: 'No', 89: 'Yes', 93: 'Yes', 95: 'Yes'}.get(flash)
    if flash == 'Yes': flash = gettext('Fired')
    if flash == 'No': flash = gettext('Off')
    return flash


app.jinja_env.filters['interpret_flash'] = interpret_flash
app.jinja_env.filters['timezoned'] = timezoned
app.jinja_env.filters['escape_slashes'] = escape_slashes


class MyIntConverter(BaseIntConverter):
    regex = r'-?(\d+)'


app.url_map.converters['myint'] = MyIntConverter


@babel.localeselector
def get_locale():
    user_locale = session.get('user_locale')
    if user_locale:
        return user_locale
    else:
        return 'ru'
    return request.accept_languages.best_match(['ru', 'en'])


ONLINE_TABLE = {}
ONLINE_SOCIAL_TABLE = {}
crd = CacheRData()


def allowed_file(filename, ext=[]):
    if ext: return '.' in filename and filename.rsplit('.', 1)[1] in ext
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def check_null(info):
    if info:
        return info
    else:
        return gettext('no info')


app.jinja_env.filters['check_null'] = check_null
app.jinja_env.filters['file_is_image'] = utils.file_is_image
app.jinja_env.filters['file_is_audio'] = utils.file_is_audio


def _validate_page(page, pages_count):
    try:
        if int(page) > pages_count:
            page = pages_count
        elif int(page) < 0:
            page = 0
        else:
            page = int(page)
    except ValueError:
        page = 0
    return page


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('nickname'):
            flash('Please Sign in')
            return redirect(url_for('sign', next=request.url))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico',
                               mimetype='image/vnd.microsoft.icon')


@app.route('/kino')
def showAfisha():
    timetable = crd.caching_retrieve()
    last_req = crd.get_last_update()
    films = timetable.keys()
    return render_template('kino.html', films=films, times=timetable, \
                           title='Megafilm', vs=timetable.values(), last_req=last_req, nickname=session.get('nickname'))


@app.route('/reallogin', methods=['GET', 'POST'])
def reallogin():
    form = RealLogin()
    if form.validate_on_submit():
        nickname = form.nickname.data
        password = form.password.data
        email = form.email.data
        try:
            core_api.register_new_user(nickname=nickname, password=password, email=email)
            session['nickname'] = nickname
            flash(gettext('Registration successfull!'))
            return redirect('/sign')
        except EmailAlreadyUsed:
            flash(gettext('User with this email already exist!'))
            return redirect('/reallogin')
        except AlreadyRegistered:
            flash(gettext('User already exitst!'))
            return redirect('/reallogin')
    return render_template('reallogin.html', form=form, title='registration', nickname=session.get('nickname'))


@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    ONLINE_TABLE[session['nickname']] = datetime.datetime.utcnow()
    online_users = [user for user, lasttime in ONLINE_TABLE.items() if \
                    lasttime + datetime.timedelta(minutes=app.config['TIMEOUT_CHAT']) > datetime.datetime.utcnow()]
    form = PostForm(prefix='form')
    if form.validate_on_submit():
        message = form.message.data
        user = core_api.get_user_by_nick(session['nickname'])
        if user:
            try:
                core_api.add_message(msg_author=user.nickname, msg_dest=None, msg_type='chat', \
                                     msg_body=form.message.data)
            except NoMessageBody:
                flash(gettext('So where your message?'))
            return redirect('/chat')
    messages = core_api.get_last_chat_messages(50)
    # online_users.extend([u'петя',u'вася',u'коля',u'паша',u'дима',u'маша',u'даша',u'вероника',u'азаза',u'за',u'за',u'за',u'заза',u'заза',u'зааз',u'азаз',u'азаз',u'азаз',u'заза',u'азаз',u'азаз',u'азаз',u'азаз',u'азаз',u'азаз',u'азаз',u'азаз',u'азаз',u'азаз',u'азаз',u'азаз',u'азаз',u'зазаазаз'])
    return render_template('chat.html', form=form, messages=messages, nickname=session.get('nickname'), \
                           online_users=online_users, title='chat')


@app.route('/ajax/chat_post_message', methods=['POST'])
def ajax_post_to_chat():
    nickname = session.get('nickname')
    message = request.form.get('msg_body')
    try:
        post = core_api.add_message(msg_author=nickname, msg_dest=None, msg_type='chat', \
                                    msg_body=message)
        rend_message = render_template("chat_message.html", message=post)
        return jsonify({"message": rend_message})
    except NoMessageBody:
        return  # TODO: change behavior for do not 502 error


@app.route('/sign', methods=['GET', 'POST'], endpoint='sign')
def sign():
    form = SignForm()
    nickname = session.get('nickname')
    cookie = request.cookies.get('nickname')
    nexturl = request.args.get('next')
    if cookie:  # if cookie and get_flashed_messages():
        s = itsdangerous.Signer(app.secret_key, salt='солюжечка')
        try:
            nickname = s.unsign(cookie)
            session['nickname'] = nickname
            get_flashed_messages()
            if nexturl:
                return redirect(nexturl)
            else:
                return redirect('/profile')
        except itsdangerous.BadSignature:
            flash(gettext('Hackors not allowed!'))
    if form.validate_on_submit():
        nickname = form.nickname.data
        password = form.password.data
        user = core_api.get_user_by_nick(nickname)
        if user:
            if password == user.password:
                session['nickname'] = nickname
                session['user_locale'] = user.language if user.language in ['en', 'ru'] else 'en'
                if nexturl:
                    response = make_response(redirect(nexturl))
                else:
                    response = make_response(redirect('/profile'))
                if form.remember_me.data:
                    s = itsdangerous.Signer(app.secret_key, salt='солюжечка')
                    signed_nickname = s.sign(nickname.encode())
                    response.set_cookie('nickname', value=signed_nickname, expires=datetime.datetime.utcnow() + \
                                                                                   datetime.timedelta(hours=app.config[
                                                                                       'COOKIE_EXPIRATION']))
                return response
            else:
                flash(gettext('Wrong password'))
                return redirect('/sign')
        else:
            flash(gettext('User do not exist'))
            return redirect('/sign')
    return render_template('sign.html', nickname=nickname, form=form, title='sign')


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if request.form.get('logout', None) == "logout":
        session.clear()
        response = make_response(redirect('/sign'))
        response.set_cookie('nickname', '', expires=0)
        return response


@app.route('/upload/<filename>', methods=['GET', 'POST'], endpoint="upload")
def uploaded_file(filename):
    abs_pathname = os.path.abspath(app.config['UPLOAD_FOLDER'])
    return send_from_directory(abs_pathname, filename)


@app.route('/thumbnails/<filename>', methods=['GET', 'POST'], endpoint="thumbnails")
def thumb_file(filename):
    abs_pathname = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], 'thumbnails/'))
    return send_from_directory(abs_pathname, filename)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    form = UploadForm()
    if request.method == 'POST':
        file = request.files['file']
        if file:
            filename = secure_filename(file.filename)
            filename = datetime.datetime.utcnow().strftime('%y.%m.%d_%H:%M:%S_') + filename
            if not len(db.session.query(models.UploadedFile.filename).filter(
                            models.UploadedFile.filename == filename).all()):
                db.session.add(models.UploadedFile(file_author=session['nickname'], filename=filename, \
                                                   access='file_exchange', upload_data=datetime.datetime.utcnow()))
                db.session.commit()
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                form.link.data = url_for('upload', filename=filename)
                if utils.file_is_image(filename):
                    utils.save_thumb(filename)
            else:
                flash(gettext('File with this filename alredy uploaded!'))
                flash(url_for('upload', filename=filename))
                return redirect('/upload')
        else:
            flash(gettext('So where is your file?'))
            return redirect('/upload')
    recent = request.args.get('recent', '')
    recent_is_image = ""
    if recent:
        recent = str(recent)
        recent_is_image = True if (recent.rsplit('.')[-1].lower() in ['jpg', 'jpeg', 'png', 'gif']) else False
    files = models.UploadedFile.query.filter_by(access='file_exchange').order_by(
        desc(models.UploadedFile.upload_data)).limit(10).all()
    return render_template('upload.html', files=files, form=form, recent=recent, title='File upload', \
                           recent_is_image=recent_is_image, nickname=session.get('nickname'))


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_page():
    if models.User.query.filter(models.User.nickname == session['nickname']).first().role == 0:
        flash(gettext('Access denied for you, sorry!'))
        return redirect('/sign')

    users_count = models.User.query.count()
    files_count = models.UploadedFile.query.count()
    pages_count = users_count / 50  # math.ceil(users_count/float(50))
    page = request.args.get('page', '')
    try:
        if int(page) > pages_count:
            page = pages_count
        elif int(page) < 0:
            page = 0
        else:
            page = int(page)
    except ValueError:
        page = 0

    users = models.User.query.order_by(desc(models.User.registration_data)).offset(page * 50).limit(50).all()
    files = models.UploadedFile.query.order_by(desc(models.UploadedFile.upload_data)).offset(page * 10).limit(10).all()
    for file in files:
        fullpathfile = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        if os.path.isfile(fullpathfile):
            file.size = utils.humansize(os.path.getsize(fullpathfile))
        else:
            file.size = 0
    return render_template('admin.html', users=users, files=files, title="Admin's panel", \
                           nickname=session.get('nickname'), pages_count=pages_count, page=page,
                           users_count=users_count, \
                           files_count=files_count)


@app.route('/admin/userinfo/<nickname>', methods=['GET', 'POST'])
@login_required
def userinfo(nickname):
    if models.User.query.filter(models.User.nickname == session['nickname']).first().role == 0:
        flash('Access denied for user: %s!' % session.get('nickname'))
        return redirect('/sign')
    if not len(db.session.query(models.User.nickname).filter(models.User.nickname == nickname).all()):
        flash('User %s not found!' % nickname)
        return redirect('/admin')
    form = SubmitForm()
    user = db.session.query(models.User).filter(models.User.nickname == nickname).first()
    if form.validate_on_submit():
        user.role = models.ROLE_ADMIN
        db.session.commit()
        flash(gettext('User was added to admin list'))
        return redirect(redirect_url())
    count_messages = db.session.query(models.Message).select_from(models.User).join(models.User.messages). \
        filter(models.User.nickname == nickname).count()
    up_files = db.session.query(models.UploadedFile).select_from(models.User).join(models.User.uploaded_files). \
        filter(models.User.nickname == nickname).all()
    return render_template('userinfo.html', title='userinfo', user=user, files=up_files, count_m=count_messages, \
                           form=form)


@app.route('/admin/fileinfo/<filename>', methods=['GET', 'POST'])
@login_required
def fileinfo(filename):
    if models.User.query.filter(models.User.nickname == session['nickname']).first().role == 0:
        flash('Access denied for user: %s!' % session.get('nickname'))
        return redirect('/sign')
    file = db.session.query(models.UploadedFile).filter(models.UploadedFile.filename == filename).first()
    if not file:
        flash(gettext('File not found!'))
        return redirect('/admin')
    if not len(file.filename):
        flash(gettext('File not found'))
        return redirect('/admin')
    fullpathfile = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    size = 0
    if os.path.isfile(fullpathfile):
        size = utils.humansize(os.path.getsize(fullpathfile))
    else:
        size = 0
    if request.args.get('delfile', '') == 'delete':
        if size:
            os.remove(fullpathfile)
            if utils.file_is_image(filename):
                os.remove()  # TODO make it
        db.session.delete(file)
        db.session.commit()
        flash(gettext('File successfully deleted!'))
        return redirect(redirect_url())
    is_image = True if (file.filename.rsplit('.')[-1].lower() in ['jpg', 'jpeg', 'png', 'gif']) else False
    return render_template('fileinfo.html', title='fileinfo', file=file, size=size, \
                           is_image=utils.file_is_image, nickname=session.get('nickname'))


@app.route('/modprofile', methods=['GET', 'POST'])
@login_required
def usermodprofile():
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    if not user:
        flash(gettext('You are not present in DB'))
        return redirect('/sign')
    form = ProfileChange()
    # validate and save
    if form.validate_on_submit():
        user_birthday = '%d.%d.%d' % (form.birth_date_day.data, form.birth_date_month.data, form.birth_date_year.data)
        user_birthday = datetime.datetime.strptime(user_birthday, '%d.%m.%Y')
        userpic = form.user_pic.data
        gender = \
        [(0, u'male'), (1, u'female'), (2, u'trans'), (3, u'cyberpunk'), (4, u'noselect')][form.user_gender.data][1]
        country = list_countries[form.user_location_country.data][1]
        city = form.user_location_city.data
        general_info = form.user_general_info.data
        interests = form.user_interests.data
        old_password = form.old_password.data
        new_password = form.new_password.data
        new_email = form.new_email.data
        phone_number = form.phone_number.data
        jid = form.jid.data
        pgpkeyid = form.pgpkeyid.data
        realname = form.realname.data
        language = form.language.data
        if new_password and not old_password:
            flash(gettext('You need old password to change it'))
            return redirect('/modprofile')
        elif new_password and old_password:
            if user.password == old_password:
                user.password = new_password
                flash(gettext('password changed!'))
            else:
                flash(gettext('wrong old password'))
                return redirect('/modprofile')
        if new_email and new_email != user.email:
            user.email = new_email
            flash(gettext('email changed'))
        if gender and gender != user.user_gender and gender != 'noselect':
            user.user_gender = gender
        if country and country != user.user_location_country:
            user.user_location_country = country
        if city and city != user.user_location_city:
            user.user_location_city = city
        if general_info and general_info != user.user_general_info:
            user.user_general_info = general_info
        if interests and interests != user.user_interests:
            user.user_interests = interests
        if user_birthday and user_birthday != user.user_birthday:
            user.user_birthday = user_birthday
        if phone_number and phone_number != user.phone_number:
            user.phone_number = phone_number
        if jid and jid != user.jid:
            user.jid = jid
        if pgpkeyid and pgpkeyid != user.pgpkeyid:
            user.pgpkeyid = pgpkeyid
        if realname and realname != user.realname:
            user.realname = ' '.join([each.capitalize() for each in realname.split()])
        if language:
            user.language = 'ru'
            session['user_locale'] = 'ru'
        else:
            user.language = 'en'
            session['user_locale'] = 'en'
        if userpic:
            filename = secure_filename(form.user_pic.data.filename)
            filename = datetime.datetime.utcnow().strftime('%y.%m.%d_%H:%M:%S_') + filename
            if not len(db.session.query(models.UploadedFile.filename).filter(
                            models.UploadedFile.filename == filename).all()):
                db.session.add(models.UploadedFile(file_author=user.nickname, filename=filename, \
                                                   upload_data=datetime.datetime.utcnow()))
                userS = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
                userS.user_pic = filename
                # open((os.path.join(app.config['UPLOAD_FOLDER'], filename)), 'a').close()
                form.user_pic.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                if utils.file_is_image(filename):
                    utils.save_thumb(filename)
        db.session.commit()
        return redirect('/modprofile')
    else:
        # fill form
        if user.user_birthday:
            if user.user_birthday is datetime.datetime:  # legacy
                year, month, day = user.user_birthday.split()[0].split('-')
            else:
                month, day, year = user.user_birthday.strftime('%D').split('/')
        else:
            month, day, year = datetime.datetime.now().strftime('%D').split('/')
        if int(year) > int(datetime.datetime.now().strftime('%y')):
            year = '19' + year
        else:
            year = '20' + year
        if user.user_gender:
            gender = {'male': 0, 'female': 1, 'trans': 2, 'cyberpunk': 3}[user.user_gender]
        else:
            gender = 3
        if user.user_location_country:
            country = [(x) for x, y in list_countries if y == user.user_location_country][0]
        else:
            country = 179
        form = ProfileChange(birth_date_day=int(day), birth_date_month=int(month), birth_date_year=year, \
                             user_gender=gender, user_location_country=country)
        form.new_email.data = user.email
        form.user_location_city.data = user.user_location_city
        form.user_general_info.data = user.user_general_info
        form.user_interests.data = user.user_interests
        userpic_path = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first().user_pic
        form.phone_number.data = user.phone_number
        form.jid.data = user.jid
        form.pgpkeyid.data = user.pgpkeyid
        form.realname.data = user.realname
        form.language.data = True if user.language == 'ru' else False

    return render_template('modprofile.html', form=form, nickname=session.get('nickname'), \
                           userpic_path=userpic_path, title='change your info')


def _add_comment_to_message(pmessage_id, msg_author, msg_body, uploaded_files):
    parent_message = models.Message.query.filter_by(msg_id=pmessage_id).first()
    if not parent_message:
        flash(gettext('No parent message found!'))
        return None
    if msg_body.startswith('#'):
        msg_body = msg_body.split(' ', 1)
        if len(msg_body) < 2:
            flash(gettext('So where your comment?'))
            return None
        reply_to, msg_body = msg_body
        try:
            reply_to = int(reply_to.strip('#'))
        except ValueError:
            flash(gettext('Reply id should be a number!'))
            return None
    else:
        reply_to = parent_message.msg_id
    if not msg_body and not uploaded_files:
        flash(gettext('So where your comment?'))
        return None
    msg_dest = parent_message.msg_author
    message = models.Message(parent_id=parent_message.msg_id, body=msg_body, msg_author=msg_author,
                             reply_to=reply_to, msg_dest=msg_dest, msg_type='comment',
                             timestamp=datetime.datetime.utcnow())
    if uploaded_files:
        message = core_api.add_all_attachments(message, uploaded_files)
    parent_message.add_comment(message)
    db.session.add(parent_message)
    db.session.commit()
    return message


@app.route('/delprofile', methods=['POST'])
@login_required
def del_profile():
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    messages = user.messages.all()
    uploaded_files = user.uploaded_files.filter_by(access='file_exchange').all()  # only exchange
    galleries = user.galleries.all()
    for message in messages:
        _delete_message(message.msg_id)
    f_messages = models.Message.query.filter_by(msg_dest=user.nickname).all()
    for message in f_messages:
        _delete_message(message.msg_id)
    for upfile in uploaded_files:
        _delfile(upfile.file_id)
    for gallery in galleries:
        _delete_gallery(gallery, user)
    db.session.delete(user)
    db.session.commit()
    session.clear()
    flash(gettext('Your profile and all signed data was removed!'))
    response = make_response(redirect('/sign'))
    response.set_cookie('nickname', '', expires=0)
    return response


@app.route('/', defaults={'nick': None, 'message_id': None}, methods=['GET', 'POST'])
@app.route('/profile', defaults={'nick': None, 'message_id': None}, methods=['GET', 'POST'], endpoint='profile')
@app.route('/profile/<nick>', defaults={'message_id': None}, methods=['GET', 'POST'])
@app.route('/profile/add_comment/<int:message_id>/<nick>', methods=['POST'])
@login_required
def userprofile(nick, message_id):
    if nick:
        user = core_api.get_user_by_nick(nick)
        if not user:
            return redirect(redirect_url())
    else:
        user = core_api.get_user_by_nick(session.get('nickname'))
    if not user:
        flash(gettext('Bad request'))
        return redirect('/profile')
    form2 = SendComment(prefix='form2')
    if form2.validate_on_submit():
        msg_author = session.get('nickname')
        msg_body = form2.comment_message_body.data
        message_file = form2.comment_message_file.data
        uploaded_files = flask.request.files.getlist('form2-comment_message_file') if message_file else None
        comment = _add_comment_to_message(message_id, msg_author, msg_body, uploaded_files)
        if not comment:
            return redirect(redirect_url())
        url = redirect_url() + '#%d' % comment.msg_id
        return redirect(url)
    form = SendMessage(prefix='form')
    if form.validate_on_submit():
        msg_author = session.get('nickname')
        msg_body = form.message_body.data
        msg_dest = nick if nick else session.get('nickname')
        msg_type = 'blog'
        uploaded_files = request.files.getlist('form-message_file')
        try:
            message = core_api.add_message(msg_author=msg_author, msg_dest=msg_dest, msg_type='blog', msg_body=msg_body,
                                           uploaded_files=uploaded_files)
        except (NoMessageBody, NoSuchUser, DestinationError):
            red_url = ('/profile/%s' % nick) if nick else '/profile'
            return redirect(red_url)
        return redirect(redirect_url() + '#%d' % message.msg_id)
    messages_q = db.session.query(models.Message).options(eagerload('comments')).options(joinedload('user')). \
        filter(models.Message.msg_dest == user.nickname).filter(models.Message.msg_type == 'blog'). \
        order_by(desc(models.Message.timestamp))
    tag = request.args.get('tag', '')
    if tag:
        messages_q = messages_q.filter(models.Message.tags.any(entity=tag))
    messages_count = messages_q.count()
    page = request.args.get('page', '')
    pages_count = messages_count / 20
    page = _validate_page(page, pages_count)
    messages = messages_q.offset(20 * page).limit(20)
    # comments_test = messages.with_entities(models.Message.comments).all()
    friend = True if nick and models.User.query.filter_by(nickname=session.get('nickname')).first().is_friend(
        user) else False
    online = _check_online([user])
    online = online[user.nickname]
    galleries = user.galleries.limit(9).all()
    for gallery in galleries:
        last_photo = gallery.photos.order_by(desc(models.UploadedFile.upload_data)).first()
        if last_photo:
            gallery.last_photo = last_photo.filename
        else:
            gallery.last_photo = None
    friends = user.friended.all()
    return render_template('profile.html', form=form, form2=form2, messages=messages, user=user, \
                           nickname=session.get('nickname'), nick=nick, title='user profile', \
                           online=online, page=page, pages_count=pages_count, friend=friend, blog=True,
                           galleries=galleries, friends=friends)


def _check_online(users_list):
    result = {}
    online_users = [usr for usr, lasttime in ONLINE_SOCIAL_TABLE.items() if \
                    lasttime + datetime.timedelta(minutes=app.config['TIMEOUT_SOCIAL'],
                                                  seconds=10) > datetime.datetime.utcnow()]
    for user in users_list:
        result[user.nickname] = user.nickname in online_users
    return result


@app.route('/messages', methods=['GET', 'POST'])
@login_required
def profile_messages():
    form = SendMessage()
    user = core_api.get_user_by_nick(session.get('nickname'))
    if form.validate_on_submit():
        msg_author = user.nickname
        msg_dest = form.message_dest.data
        msg_body = form.message_body.data
        uploaded_files = flask.request.files.getlist('message_file')
        try:
            message = core_api.add_message(msg_author=msg_author, msg_dest=msg_dest, msg_type='private',
                                           msg_body=msg_body,
                                           uploaded_files=uploaded_files)
            return redirect('/messages/%s' % msg_dest)
        except DestinationError:
            flash(gettext('You need fill destination field'))
            return redirect(redirect_url())
        except NoSuchUser:
            flash(gettext('No such username, you should specify a real user name'))
            return redirect(redirect_url())
        except NoMessageBody:
            flash(gettext('So where your message?'))
            return redirect(redirect_url())
    else:
        pass

    posted = db.session.query(models.Message).filter(models.Message.msg_author == user.nickname). \
        filter(models.Message.msg_type == 'private').filter(models.Message.del_from_author == False)
    recieved = db.session.query(models.Message).filter(models.Message.msg_dest == user.nickname). \
        filter(models.Message.msg_type == 'private').filter(models.Message.del_from_dest == False)
    page = request.args.get('page', '')
    messages_q = posted.union(recieved).order_by(desc(models.Message.timestamp)).options(joinedload('user')).options(
        eagerload('comments'))
    messages_count = messages_q.count()
    pages_count = messages_count / 20
    page = _validate_page(page, pages_count)
    all_messages = messages_q.offset(page * 20).limit(20)
    for message in all_messages:
        if message.msg_author != user.nickname and not message.is_read:
            message.is_read = True
            db.session.add(message)
    db.session.commit()
    return render_template('messages.html', form=form, messages=all_messages, user=user, nickname=user.nickname, \
                           page=page, pages_count=pages_count, title='messages')


@app.route('/messages/<nick>', methods=['GET', 'POST'])
@login_required
def private_messages(nick):
    form = SendMessage()
    user = core_api.get_user_by_nick(session.get('nickname'))
    dest_user = core_api.get_user_by_nick(nick)
    if not dest_user:
        return redirect('/messages')
    if user.nickname == nick:
        return redirect('/messages')
    if form.validate_on_submit():
        msg_author = user.nickname
        msg_dest = nick
        msg_body = form.message_body.data
        uploaded_files = flask.request.files.getlist('message_file')
        try:
            message = core_api.add_message(msg_author=msg_author, msg_dest=msg_dest, msg_type='private',
                                           msg_body=msg_body,
                                           uploaded_files=uploaded_files)
            return redirect(redirect_url())
        except NoMessageBody:
            flash(gettext('So where your message?'))
            return redirect(redirect_url())
    else:
        pass
    if not user:
        flash(gettext('You are not present in DB'))
        return redirect('/sign')
    posted = db.session.query(models.Message).filter(models.Message.msg_author == user.nickname). \
        filter(models.Message.msg_type == 'private').filter(models.Message.msg_dest == nick). \
        filter(models.Message.del_from_author == False)
    recieved = db.session.query(models.Message).filter(models.Message.msg_dest == user.nickname). \
        filter(models.Message.msg_author == nick).filter(models.Message.msg_type == 'private'). \
        filter(models.Message.del_from_dest == False)
    page = request.args.get('page', '')
    messages_q = posted.union(recieved).order_by(desc(models.Message.timestamp)).options(joinedload('user')).options(
        eagerload('comments'))
    messages_count = messages_q.count()
    pages_count = messages_count / 20
    page = _validate_page(page, pages_count)
    all_messages = messages_q.offset(20 * page).limit(20)
    for message in all_messages:
        if message.msg_author != user.nickname and not message.is_read:
            message.is_read = True
            db.session.add(message)
    db.session.commit()
    online = _check_online([models.User.query.filter_by(nickname=nick).first()])
    online = online[nick]
    return render_template('messages.html', private=True, form=form, messages=all_messages, user=user,
                           nickname=user.nickname, page=page, pages_count=pages_count, friend=nick, title='messages',
                           online=online)


def _delete_message(id):
    message = db.session.query(models.Message).filter(models.Message.msg_id == id).first()
    if not message:
        flash(gettext('Hackers not allowed!'))
        return 'redirect'
    current_user = session.get('nickname')
    if message.msg_type == 'private':
        if message.msg_author == current_user and message.msg_dest == current_user:  # message, sent to himself
            message.del_from_author = True
            message.del_from_dest = True
        elif message.msg_author == current_user:
            message.del_from_author = True
        else:  # message.msg_dest == current_user
            message.del_from_dest = True
        if message.del_from_author and message.del_from_dest:
            db.session.delete(message)
            if message.attachment:  # legacy
                _delfile(message.attachment.file_id)
            attachments = message.attachments.all()
            if len(attachments):
                for attachment in attachments:
                    _delfile(attachment.file_id)
            tags = message.tags
            for tag in tags:
                q, w = message.remove_tag(tag)
                if q:
                    db.session.add(w)
                else:
                    db.session.execute(w)
    if message.msg_type == 'group':
        owner = message.group.owner
        author = message.msg_author
        if owner == current_user or author == current_user:
            _delete_all_data_message(message)
        else:
            flash(gettext('Operation not permitted'))
            return 'redirect'
    if message.msg_type == 'blog' or message.msg_type == 'comment':
        if message.msg_author == current_user or message.msg_dest == current_user:
            _delete_all_data_message(message)
        else:
            flash(gettext('Operation not permitted'))
            return 'redirect'


def _delete_all_data_message(message):
    if message.attachment:  # legacy
        if utils.file_is_image(message.attachment):
            _delfile(message.attachment.file_id)
    attachments = message.attachments.all()
    if len(attachments):
        for attachment in attachments:
            _delfile(attachment.file_id)
    tags = message.tags
    for tag in tags:
        q, w = message.remove_tag(tag)
        if q:
            db.session.add(w)
        else:
            db.session.execute(w)
    comments = message.comments
    if comments:
        for comment in comments:
            attachments = comment.attachments.all()
            if len(attachments):
                for attachment in attachments:
                    _delfile(attachment.file_id)
            db.session.delete(comment)
    db.session.delete(message)


@app.route('/delmessage/<int:id>', methods=['POST'])
@login_required
def delete_message_view(id):
    res = _delete_message(id)
    if res == 'redirect':
        return redirect(redirect_url())
    db.session.commit()
    return redirect(redirect_url())


@app.route('/ajax/delmessage', methods=['POST'])
@login_required
def ajax_delete_message():
    message_id = request.form.get('id')
    res = _delete_message(int(message_id))
    errors = None
    if res == 'redirect':
        errors = get_flashed_messages()
    if not errors:
        db.session.commit()
    return jsonify({'response': message_id, 'errors': errors})


@app.route('/friends', methods=['GET', 'POST'])
@login_required
def friends():
    user = models.User.query.filter_by(nickname=session.get('nickname')).first()
    form = SearchForm()
    if request.args.get('clear') == 'clear':
        return redirect('/friends')
    name = request.args.get('nickname')
    req = user.friended
    if name:
        req1 = req.filter(models.User.nickname.like('%' + name + '%'))
        req2 = req.filter(models.User.realname.like('%' + name + '%'))
        req = req1.union(req2)
    friends_count = req.count()
    page = request.args.get('page', '')
    pages_count = friends_count / 30
    page = _validate_page(page, pages_count)
    friends = req.offset(page * 30).limit(30).all()
    online = _check_online(friends)
    return render_template('friends.html', friends=friends, friends_count=friends_count, page=page, \
                           online=online, pages_count=pages_count, nickname=user.nickname, title='friends', form=form)


@app.route('/addfriend/<nick>', methods=['POST'])
@login_required
def addfriend(nick):
    user = models.User.query.filter_by(nickname=nick).first()
    me = models.User.query.filter_by(nickname=session.get('nickname')).first()
    if not user or not me:
        flash('Incorrect Request')
        return redirect(redirect_url())
    if nick == me.nickname:
        flash('You can not friend myself')
        return redirect(redirect_url())
    u = me.to_friend(user)
    if not u:
        flash(gettext('Cant friend'))
        return redirect(redirect_url())
    db.session.add(u)
    message = models.Message(
        body=f'Service message. User {me.nickname} added you to friends.\n \
            Сервисное сообщение. Пользователь {me.nickname} добавил вас в друзья.',
        msg_author=me.nickname,
        msg_dest=user.nickname,
        msg_type='private',
        timestamp=datetime.datetime.utcnow(),
        del_from_author=True,
        del_from_dest=False,
    )
    db.session.add(message)
    db.session.commit()
    flash(gettext('Friended'))
    return redirect(redirect_url())


@app.route('/delfriend/<nick>', methods=['GET', 'POST'])
@login_required
def delfriend(nick):
    user = models.User.query.filter_by(nickname=nick).first()
    me = models.User.query.filter_by(nickname=session.get('nickname')).first()
    if not user or not me:
        flash(gettext('Incorrect request'))
        return redirect(redirect_url())
    u = me.to_ufriend(user)
    if not u:
        flash(gettext('Cant unfriend'))
        return redirect(redirect_url())
    db.session.add(u)
    db.session.commit()
    flash(gettext('Removed from friends'))
    return redirect(redirect_url())


@app.route('/photogallery', methods=['GET', 'POST'])
@login_required
def photogallery():
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    form = PhotoGallery()
    if form.validate_on_submit():
        name = form.name.data
        info = form.info.data
        location = form.location.data
        if name:
            pg = models.PhotoGallery(author=user.nickname, upload_date=datetime.datetime.utcnow(), \
                                     name=name, info=info, location=location)
            db.session.add(pg)
        else:
            flash('noname!')
            redirect(redirect_url())
        db.session.commit()
        return redirect(redirect_url())
    page = request.args.get('page', '')
    galleries_count = user.galleries.count()
    pages_count = galleries_count / 10
    page = _validate_page(page, pages_count)
    galleries = user.galleries.offset(page * 10).limit(10).all()
    for gallery in galleries:
        last_photo = gallery.photos.order_by(desc(models.UploadedFile.upload_data)).first()
        if last_photo:
            gallery.last_photo = last_photo.filename
        else:
            gallery.last_photo = None
    return render_template('photogallery.html', form=form, nickname=user.nickname, galleries=galleries, \
                           pages_count=pages_count, page=page, title=gettext('photogalleries'))


@app.route('/photogallery/<nick>', methods=['GET', 'POST'])
@login_required
def friend_photogallery(nick):
    user = db.session.query(models.User).filter_by(nickname=nick).first()
    if not user:
        flash(gettext('Bad request, no such user'))
        return redirect('/photogallery')
    me = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    friend = True if me.is_friend(user) else False
    page = request.args.get('page', '')
    galleries_count = user.galleries.count()
    pages_count = galleries_count / 10
    page = _validate_page(page, pages_count)
    galleries = user.galleries.offset(page * 10).limit(10).all()
    for gallery in galleries:
        last_photo = gallery.photos.order_by(desc(models.UploadedFile.upload_data)).first()
        if last_photo:
            gallery.last_photo = last_photo.filename
        else:
            gallery.last_photo = None
    return render_template('photogallery.html', nick=nick, nickname=session.get('nickname'), galleries=galleries, \
                           friend=friend, pages_count=pages_count, page=page, title=gettext('photogalleries'))


@app.route('/gallery/<int:id>', methods=['GET', 'POST'])
@login_required
def gallery(id):
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    gallery = models.PhotoGallery.query.filter(models.PhotoGallery.id == id).first()
    if not gallery:
        flash(gettext('Bad request'))
        return redirect(redirect_url())
    guest = True if (user.nickname != gallery.author) else False
    gallery_author = db.session.query(models.User).filter_by(nickname=gallery.author).first()
    friend = True if user.is_friend(gallery_author) else False
    form = Gallery()
    if form.validate_on_submit():
        if user.nickname != gallery.author:
            flash(gettext('Bad request'))
            return redirect(redirect_url())
        uploaded_files = flask.request.files.getlist('new_photo')
        gallery = core_api.add_all_attachments(gallery, uploaded_files)
        db.session.commit()
        photos_count = gallery.photos.count() - 1
        pages_count = photos_count / 50
        url = redirect_url().split('?page', 1)[0]
        return redirect(url + '?page=' + str(pages_count))
    tag = request.args.get('tag', '')
    req = gallery.photos
    if tag:
        req = req.filter(models.UploadedFile.tags.any(entity=tag))
    page = request.args.get('page', '')
    photos_count = req.count() - 1
    pages_count = photos_count / 50
    page = _validate_page(page, pages_count)
    photos = req.offset(page * 50).limit(50).all()
    if tag:
        for photo in photos:
            photo.offset = gallery.photos.all().index(photo)
    return render_template('gallery.html', form=form, gallery=gallery, nickname=user.nickname, \
                           tag=tag, photos=photos, page=page, pages_count=pages_count, guest=guest, friend=friend, \
                           title='gallery')


def _add_comment(comment, photo):
    c = models.Comment(author=session.get('nickname'), date=datetime.datetime.utcnow(), body=comment)
    db.session.add(c)
    additional = photo.add_comment(c)
    db.session.add(additional)


@app.route('/gallery/<int:id>/<myint:photonum>', methods=['GET', 'POST'])
@login_required
def photo(id, photonum):
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    gallery = models.PhotoGallery.query.filter(models.PhotoGallery.id == id).first()
    gallery_author = db.session.query(models.User).filter_by(nickname=gallery.author).first()
    friend = True if user.is_friend(gallery_author) else False
    if not gallery:
        flash(gettext('Bad request'))
        return redirect(redirect_url())
    form = Photo()
    photo_count = gallery.photos.count()
    if photonum > photo_count - 1 or photonum < 0:
        return redirect('/gallery/%d' % id)
    photo = gallery.photos.offset(photonum).limit(1).first()
    if form.validate_on_submit():
        comment = form.comment.data
        if comment:
            _add_comment(comment, photo)
        else:
            flash(gettext('So where is your comment?'))
            return redirect(redirect_url())
        db.session.commit()
        return redirect(redirect_url())
    comments = photo.comments.order_by(models.Comment.date)
    guest = True if (photo.file_author != user.nickname) else False
    return render_template('photo.html', nickname=user.nickname, gallery=gallery, photo=photo, \
                           form=form, photonum=photonum, comments=comments, guest=guest, friend=friend,
                           title='photo view')


@app.route('/delfile/<id>', methods=['GET', 'POST'])
@login_required
def delfile(id):
    _delfile(id)
    return redirect(redirect_url())


def _delfile(id):
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    file = db.session.query(models.UploadedFile).filter_by(file_id=id).first()
    if not file:
        flash(gettext('Bad request'))
        return redirect(redirect_url())
    message = file.message
    if not message and file.file_author != user.nickname:
        flash(gettext('Hackors not allowed'))
        return redirect(redirect_url())
    if message and message.msg_dest != user.nickname and message.msg_author != user.nickname:
        flash(gettext('Hackors not allowed'))
        return redirect(redirect_url())
    core_api._remove_from_disk(file.filename)
    comments = file.comments.all()
    if comments:
        for comment in comments:  # sqlite and mysql don't support cascade removal
            db.session.delete(comment)
    tags = file.tags.all()
    if tags:
        for tag in tags:
            q, w = file.remove_tag(tag)
            if q:
                db.session.add(w)
            else:
                db.session.execute(w)
    if file.exif:
        db.session.delete(file.exif)
    db.session.delete(file)
    db.session.commit()


@app.route('/delcomment/<int:id>', methods=['GET', 'POST'])
@login_required
def delcomment(id):
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    comment = db.session.query(models.Comment).filter_by(id=id).first()
    if not comment:
        flash(gettext('Bad request'))
        return redirect(redirect_url())
    if user.nickname != comment.author and user.nickname != comment.file[0].file_author:
        flash(gettext('Hackors not allowed'))
        return redirect(redirect_url())
    db.session.delete(comment)
    db.session.commit()
    return redirect(redirect_url())


@app.route('/delcomment_from_author/<int:id>', methods=['GET', 'POST'])
@login_required
def delcomment_from_author(id):
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    comment = db.session.query(models.Comment).filter_by(id=id).first()
    if not comment or not user:
        flash(gettext('Bad request'))
        return redirect(redirect_url())
    if user.nickname != comment.author and user.nickname != comment.file[0].file_author:
        flash(gettext('Hackors not allowed'))
        return redirect(redirect_url())
    comments = comment.file[0].comments.filter(models.Comment.author == comment.author).all()
    for each in comments:
        db.session.delete(each)
    db.session.commit()
    return redirect(redirect_url())


@app.route('/delcomment_all/<int:photo_id>', methods=['GET', 'POST'])
@login_required
def delcomment_all(photo_id):
    _delcomment_all(photo_id)
    return redirect(redirect_url())


def _delcomment_all(photo_id):
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    photo = db.session.query(models.UploadedFile).filter_by(file_id=photo_id).first()
    if not photo:
        flash(gettext('Bad request'))
        return redirect(redirect_url())
    if user.nickname != photo.file_author:
        flash(gettext('Hackors not allowed'))
        return redirect(redirect_url())
    comments = photo.comments.all()
    for comment in comments:
        db.session.delete(comment)
    db.session.commit()


@app.route('/delgallery/<int:id>', methods=['GET', 'POST'])
@login_required
def delgallery(id):
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    gallery = db.session.query(models.PhotoGallery).filter_by(id=id).first()
    _delete_gallery(gallery, user)
    return redirect(redirect_url())


def _delete_gallery(gallery, user):
    if not gallery:
        flash(gettext('Bad request'))
        return 'redirect'
    if user.nickname != gallery.author:
        flash(gettext('Hackors not allowed'))
        return 'redirect'
    photos = gallery.photos.all()
    for photo in photos:
        _delfile(photo.file_id)
    db.session.delete(gallery)
    db.session.commit()
    return 'ok'


@app.route('/rotateimage/<id>/<int:clockwise>', methods=['POST', 'GET'])
@login_required
def rotateimage(id, clockwise):
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    photo = db.session.query(models.UploadedFile).filter_by(file_id=id).first()
    if not photo:
        flash(gettext('Bad request'))
        return redirect(redirect_url())
    if user.nickname != photo.file_author:
        flash(gettext('Hackors not allowed'))
        return redirect(redirect_url())
    old_filename = photo.filename
    if utils.file_is_image(photo.filename):
        with wand.image.Image(filename=os.path.join(app.config['UPLOAD_FOLDER'], photo.filename)) as img:
            with img.clone() as rotated:
                if clockwise == 0:
                    rotated.rotate(90)
                elif clockwise == 1:
                    rotated.rotate(-90)
                photo.filename = datetime.datetime.utcnow().strftime('%y.%m.%d_%H:%M:%S_') + \
                                 photo.filename.split('_', 2)[2]
                rotated.save(filename=os.path.join(app.config['UPLOAD_FOLDER'], photo.filename))
        utils.save_thumb(photo.filename)
    core_api._remove_from_disk(old_filename)
    db.session.add(photo)
    db.session.commit()
    return redirect(redirect_url())


@app.route('/people', methods=['GET', 'POST'])
@login_required
def people():
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    form = SearchForm()
    if request.args.get('clear') == 'clear':
        return redirect('/people')
    nickname = request.args.get('nickname')
    realname = request.args.get('realname')
    age = request.args.get('age')
    ageless = request.args.get('ageless')
    req = models.User.query
    if nickname:
        req = req.filter(models.User.nickname.like('%' + nickname + '%'))
    if realname:
        req = req.filter(models.User.realname.like('%' + realname + '%'))
    if age:
        req = req.filter(models.User.user_birthday < datetime.datetime.now() - relativedelta(years=int(age)))
    if ageless:
        req = req.filter(models.User.user_birthday > datetime.datetime.now() - relativedelta(years=int(ageless)))
    page = request.args.get('page', '')
    people_count = req.count()
    pages_count = people_count / 100
    page = _validate_page(page, pages_count)
    people = req.offset(page * 100).limit(100).all()
    online = _check_online(people)
    return render_template('people.html', user=user, people=people, people_count=people_count, nickname=user.nickname,
                           online=online, page=page, pages_count=pages_count, form=form, title='people search')


@app.route('/testajax', methods=['POST'])
@login_required
def test():
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    msg_id = request.form.get('msg_id')
    ONLINE_TABLE[session['nickname']] = datetime.datetime.utcnow()
    if not msg_id:
        msg_id = 0;
    messages = models.Message.query.filter(models.Message.msg_type == 'chat'). \
        filter(models.Message.msg_author != user.nickname).filter(models.Message.msg_id > msg_id)
    if messages:
        result = ''
        for message in messages.all():
            result += '<span id="message">[' + str(
                message.timestamp) + ']<font color="#9C0064">&lt;' + message.msg_author + '&gt;</font><span style="white-space: pre-wrap">' + message.body + '\n' + '</span><span style="display: none;" id="msg_id">|' + str(
                message.msg_id) + '</span></span>'
        return jsonify({'text': result})
    else:
        return jsonify({})


@app.route('/unread_messages_count', methods=['POST'])
@login_required
def unread_messages():
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    ONLINE_SOCIAL_TABLE[session['nickname']] = datetime.datetime.utcnow()
    msg_count = db.session.query(models.Message).filter_by(msg_dest=user.nickname). \
        filter_by(msg_type='private').filter_by(is_read=False).count()
    return jsonify({'count': msg_count})


@app.route('/get_recent_messages', methods=['POST'])
@login_required
def get_messages():
    # nick = request.form.get('nick')
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    messages = db.session.query(models.Message).filter_by(msg_dest=user.nickname). \
        filter_by(msg_type='private').filter_by(is_read=False).all()
    count = db.session.query(models.Message).filter_by(msg_dest=user.nickname). \
        filter_by(msg_type='private').filter_by(is_read=False).count()
    for message in messages:
        message.is_read = True
        db.session.add(message)
    db.session.commit()
    html = render_template('message.html', messages=messages, nickname=user.nickname)
    return jsonify({'message': html})


def _search_images(req, tags, camera_model, lens_model, iso_from, iso_to, size):
    req = req.join(models.Exif.photo).filter(or_(models.UploadedFile.access == None, \
                                                 models.UploadedFile.access == 'public'))  # or_ models.UploadedFile.access == None -> is legacy
    if tags:
        tags, null = _truncate_tags(tags)
        for tag in tags:
            req = req.join(models.Exif.photo).join(models.UploadedFile.tags). \
                filter(models.UploadedFile.tags.any(entity=tag))
        req = req.distinct()
    if camera_model and camera_model != 'select':
        req = req.filter(models.Exif.model == camera_model)
    if lens_model and lens_model != 'select':
        req = req.filter(models.Exif.lens_model == lens_model)
    if iso_from:
        req = req.filter(models.Exif.iso > iso_from)
    if iso_to:
        req = req.filter(models.Exif.iso < iso_to)
    if size and size != 0:
        if size == '1':
            req = req.filter(models.Exif.height * models.Exif.width < 350000)
        elif size == '2':
            req = req.filter(models.Exif.height * models.Exif.width >= 350000). \
                filter(models.Exif.height * models.Exif.width < 2000000)
        elif size == '3':
            req = req.filter(models.Exif.height * models.Exif.width >= 2000000). \
                filter(models.Exif.height * models.Exif.width < 5000000)
        elif size == '4':
            req = req.filter(models.Exif.height * models.Exif.width >= 5000000). \
                filter(models.Exif.height * models.Exif.width < 8900000)
        elif size == '5':
            req = req.filter(models.Exif.height * models.Exif.width >= 8900000)
    return req


@app.route('/search_images', methods=['GET', 'POST'])
@login_required
def search_images():
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    form = ImageSearchForm()
    camera_list = [f[0] for f in models.Exif.query.filter(models.Exif.model != 'None').with_entities(
        models.Exif.model).distinct().all()]
    camera_list.insert(0, 'select')
    lens_list = [f[0] for f in models.Exif.query.filter(models.Exif.lens_model != 'None').with_entities(
        models.Exif.lens_model).distinct().all()]
    lens_list.insert(0, 'select')
    form.camera_model.choices = zip(camera_list, camera_list)
    form.lens_model.choices = zip(lens_list, lens_list)

    req = models.Exif.query
    if request.args.get('clear') == gettext('clear'):
        return redirect('/search_images')
    camera = request.args.get('camera_model')
    lens = request.args.get('lens_model')
    size = request.args.get('size')
    iso_from = request.args.get('iso_from')
    iso_to = request.args.get('iso_to')
    tags = request.args.get('tags')
    exifs = _search_images(req, tags, camera, lens, iso_from, iso_to, size)
    exifs = exifs.options(eagerload('photo'))
    if not iso_from: iso_from = 'None'
    if not iso_to: iso_to = 'None'
    if not tags:
        tags = 'None'
    else:
        tags = _encode_tags(tags)
    photos_count = exifs.count()
    if lens: lens = lens.encode('hex')
    return render_template('image_search.html', form=form, exifs=exifs, camera=camera, lens=lens, \
                           iso_from=iso_from, iso_to=iso_to, size=size, tags=tags, nickname=user.nickname, \
                           photos_count=photos_count, title='image search')


def _encode_tags(tags):
    tags, null = _truncate_tags(tags)
    if tags:
        tags = [tag.strip('#') for tag in tags]
        tags = ','.join(tags)
    return tags


def _decode_tags(tags):
    tags = tags.split(',')
    tags = ['#' + tag for tag in tags]
    tags = ' '.join(tags)
    return tags


@app.route('/search_images/virtual_gallery/<path:camera>/<path:lens>/<iso_from>/<iso_to>/<size>/<path:tags>/<myint:id>', \
           methods=['GET', 'POST'])
@login_required
def virtual_gallery(id, camera=None, lens=None, iso_from=None, iso_to=None, size=None, tags=None):
    if iso_from == 'None': iso_from = None
    if iso_to == 'None': iso_to = None
    if tags == 'None': tags = None
    if camera == 'None': camera = 'select'
    if lens == 'None':
        lens = 'select'
    else:
        if lens != 'select':
            lens = lens.decode('hex')
    if tags: tags = _decode_tags(tags)
    id = int(id)
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    form = Photo()
    req = models.Exif.query
    exifs = _search_images(req, tags, camera, lens, iso_from, iso_to, size)
    if id > exifs.count() - 1 or id < 0:
        # return redirect('/search_images?tags=%s&camera_model=%s&lens_model=%s&iso_from=%s&iso_to=%s&size=%s&submit=to+search'\
        #		% (tag, camera, lens, iso_from, iso_to, size))
        # return redirect('/search_images?tags=%s&camera_model=%s' % (tags, camera))#
        return redirect('/search_images')
    exif = exifs.offset(id).limit(1).first()
    exif_author = db.session.query(models.User).filter_by(nickname=exif.photo.file_author).first()
    friend = True if user.is_friend(exif_author) else False
    photo = exif.photo
    comments = photo.comments.order_by(models.Comment.date)
    guest = True if (photo.file_author != user.nickname) else False
    if form.validate_on_submit():
        comment = form.comment.data
        if comment:
            _add_comment(comment, photo)
        else:
            flash(gettext('So where is your comment?'))
            return redirect(redirect_url())
        db.session.commit()
        return redirect(redirect_url())
    if tags: tags = _encode_tags(tags)
    return render_template('virtual_photo.html', photo=photo, form=form, photonum=id, camera=camera, lens=lens, \
                           iso_from=iso_from, iso_to=iso_to, size=size, tags=tags, nickname=user.nickname, \
                           friend=friend, comments=comments, guest=guest, title='virtual gallery')


@app.route('/search_images/virtual_gallery/message/<int:message_id>/<myint:offset>', methods=['GET', 'POST'])
@login_required
def virtual_gallery_message(message_id, offset):
    message = db.session.query(models.Message).filter_by(msg_id=message_id).first()
    if not message:
        flash(gettext('No such message'))
        return redirect(redirect_url())
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    if message.msg_type == 'private' and message.msg_author != user.nickname and message.msg_dest != user.nickname:
        flash(gettext('Hackors not allowed!'))
        return redirect(redirect_url())
    req = message.attachments.filter(models.UploadedFile.mimetype.in_(utils.IMAGES)).order_by(
        models.UploadedFile.file_id)
    if offset > req.count() - 1 or offset < 0:
        if message.msg_type == 'blog' or message.msg_type == 'comment':
            return redirect('profile/%s#%s' % (message.msg_dest, str(message.msg_id)))
        elif message.msg_type == 'private':
            opponent = message.msg_author if (message.msg_author != user.nickname) else message.msg_dest
            return redirect('/messages/%s#%s' % (opponent, str(message.msg_id)))
    form = Photo()
    photo = req.offset(offset).limit(1).first()
    if form.validate_on_submit():
        comment = form.comment.data
        if comment:
            _add_comment(comment, photo)
        else:
            flash(gettext('So where is your comment?'))
            return redirect(redirect_url())
        db.session.commit()
        return redirect(redirect_url())
    guest = (photo.file_author != user.nickname)
    comments = photo.comments.order_by(models.Comment.date)
    return render_template('virtual_photo_message.html', photo=photo, form=form, comments=comments, guest=guest, \
                           message_id=message.msg_id, photonum=offset, nickname=user.nickname, title='virtual gallery')


@app.route('/chat/history', methods=['GET'])
@login_required
def chat_history():
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    page = request.args.get('page', '')
    req = models.Message.query.filter_by(msg_type='chat')
    messages_count = req.count()
    pages_count = messages_count / 100
    page = _validate_page(page, pages_count)
    messages = req.order_by(desc(models.Message.timestamp)).offset(page * 100).limit(100).all()
    return render_template('chat_history.html', messages=messages, page=page, nickname=user.nickname,
                           pages_count=pages_count, title='history')


@app.route('/ajax/get_photo_name', methods=['POST'])
@login_required
def ajax_get_photo_name():
    photo_id = request.form.get('photo_id')
    if not photo_id:
        response = jsonify({'code': 404, 'text': 'Not found!'})
        response.status_code = 404
        return response
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    photo = db.session.query(models.UploadedFile).filter_by(file_id=photo_id).first()
    if not photo:
        return jsonify({'text': 'error'})
    if photo.file_author != user.nickname:
        response = jsonify({'code': 403, 'text': 'Forbidden!'})
        response.status_code = 403
        return response
    tags = photo.tags.with_entities(models.Tag.entity).all()
    result = ''
    if tags:
        result += ' '.join(['#' + tag[0] for tag in tags])
        result += ' '
    result += photo.name if photo.name else photo.filename.split('_', 2)[2]
    return jsonify({'text': result})


@app.route('/ajax/set_photo_name', methods=['POST'])
@login_required
def ajax_set_photo_name():
    photo_id = request.form.get('photo_id')
    if not photo_id:
        response = jsonify({'code': 404, 'text': 'Not found!'})
        response.status_code = 404
        return response
    name = request.form.get('name')
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    photo = db.session.query(models.UploadedFile).filter_by(file_id=photo_id).first()
    if photo.file_author != user.nickname:
        response = jsonify({'code': 403, 'text': 'Forbidden!'})
        response.status_code = 403
        return response
    tags, name = _truncate_tags(name)
    old_tags = photo.tags.all()
    for tag in old_tags:
        q, w = photo.remove_tag(tag)
        if q:
            db.session.add(w)
        else:
            db.session.execute(w)
    db.session.add(photo)
    db.session.commit()
    if tags:
        for tag in tags:
            q, w = photo.add_tag(models.Tag(entity=tag))
            if q:
                db.session.add(w)
            else:
                db.session.execute(w)
    photo.name = name if name else photo.filename.split('_', 2)[2]
    db.session.add(photo)
    db.session.commit()
    # tags = [tag[0] for tag in photo.tags.with_entities(models.Tag.entity).all()]
    return jsonify({'text': photo.name, 'tags': tags})


@app.route('/addfile_to_message/<int:message_id>', methods=['POST'])
@login_required
def add_file_to_message(message_id):
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    message = models.Message.query.filter_by(msg_id=message_id).first()
    if not message:
        flash(gettext('Error, message not found!'))
        return redirect(redirect_url())
    if message.msg_author != user.nickname:
        flash(gettext('Hackors not allowed!'))
        return redirect(redirect_url())
    access = message.msg_type == 'private'
    uploaded_files = flask.request.files.getlist('new_file')
    if uploaded_files:
        core_api.update_message_attachments(message, uploaded_files, access)
    return redirect(redirect_url())


@app.route('/ajax/post_message', methods=['POST'])
@login_required
def ajax_post_message():
    msg_author = session.get('nickname')
    msg_body = request.form.get('message')
    nick = request.form.get('nick')
    msg_dest = nick if nick else msg_author
    uploaded_files = request.files.values()
    is_group = request.form.get('is_group') == 'true';
    msg_type = 'group' if is_group else 'blog'
    try:
        message = core_api.add_message(msg_author=msg_author, msg_dest=msg_dest, msg_type=msg_type, msg_body=msg_body,
                                       uploaded_files=uploaded_files)
    except (DestinationError, NoMessageBody, NoSuchUser):
        errors = get_flashed_messages()
        return jsonify({'error': errors})
    html = render_template('message.html', messages=[message], nickname=session.get('nickname'), blog=True, ajax=True)
    return jsonify({'response': html})


@app.route('/ajax/post_comment', methods=['POST'])
@login_required
def ajax_post_comment():
    msg_author = session.get('nickname')
    message_id = request.form.get('parent_id')
    nick = request.form.get('nick')
    msg_body = request.form.get('form2-comment_message_body')
    uploaded_files = request.files.values()
    app.logger.info('%s' % uploaded_files)
    comment = _add_comment_to_message(message_id, msg_author, msg_body, uploaded_files)
    if not comment:
        errors = get_flashed_messages()
        return jsonify({'error': errors})
    html = render_template('comment.html', comment=comment, nick=nick, nickname=msg_author)
    return jsonify({'response': html})


@app.route('/ajax/post_private_message', methods=['POST'])
@login_required
def ajax_post_private_message():
    msg_author = session.get('nickname')
    msg_dest = request.form.get('msg_dest')
    msg_body = request.form.get('message')
    uploaded_files = request.files.values()
    try:
        message = core_api.add_message(msg_author=msg_author, msg_dest=msg_dest, msg_type='private', msg_body=msg_body,
                                       uploaded_files=uploaded_files)
    except (NoMessageBody, NoSuchUser, DestinationError) as exc:
        errors = get_flashed_messages() or repr(exc)
        return jsonify({'error': errors})
    html = render_template('message.html', messages=[message], nickname=msg_author, blog=False)
    return jsonify({'response': html})


@app.route('/news', methods=['GET', 'POST'])
@login_required
def news():
    nickname = session.get('nickname')
    parent_message = aliased(models.Message)
    com = aliased(models.Message.comments)
    comments_to_my_messages = models.Message.query.filter_by(msg_type='blog').outerjoin(parent_message, parent_message. \
                                                                                        parent_id == models.Message.msg_id).filter(
        models.Message.msg_author == nickname).outerjoin(com, com.parent_id == models.Message.msg_id).with_entities(com)
    comments_to_other_messages = models.Message.query.filter_by(msg_type='blog').outerjoin(parent_message,
                                                                                           parent_message. \
                                                                                           parent_id == models.Message.msg_id).filter(
        parent_message.msg_author == nickname).filter(models.Message. \
                                                      msg_dest != nickname).outerjoin(com,
                                                                                      com.parent_id == models.Message.msg_id).with_entities(
        com)
    # friends_blogs_messages = models.User.query.filter_by(nickname=nickname).first().friended.with_entities(models.Message).\
    #		filter(models.Message.msg_type=='blog', models.Message.msg_dest == models.Message.msg_author, models.Message.\
    #		msg_author != nickname)
    all_comments = comments_to_my_messages.union(comments_to_other_messages)
    friends_blogs_messages = models.Message.query
    friends = models.User.query.filter_by(nickname=nickname).first().friended.all()
    for friend in friends:
        temp = friend.messages.filter_by(msg_type='blog')
        all_comments = all_comments.union(temp)
    all_comments = all_comments.order_by(desc(models.Message.timestamp)).limit(30).all()
    all_comments = filter(lambda x: x is not None, all_comments)
    for comment in all_comments:
        comment.sort_key = comment.timestamp
        comment.typeofnews = 'message'
    gallery = aliased(models.PhotoGallery)
    photos = models.User.query.filter_by(nickname=nickname).first().friended.outerjoin(gallery).with_entities(gallery). \
        outerjoin(gallery.photos).with_entities(models.UploadedFile).order_by(desc(models.UploadedFile.upload_data)). \
        limit(30).all()
    if photos:
        photos = [x for x in photos if x]
        for photo in photos:
            photo.sort_key = photo.upload_data
            photo.typeofnews = 'photo'
    news_list = list(all_comments)
    news_list.extend(photos)
    news_list.sort(key=lambda x: x.sort_key, reverse=True)
    news_list = news_list[:30]
    return render_template('news.html', news_list=news_list, nickname=nickname, title='news')


@app.route('/groups', methods=['POST', 'GET'])
@login_required
def group_list():
    groups = models.Group.query
    form = CreateGroup()
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    if form.validate_on_submit():
        name = form.name.data
        description = form.description.data
        if not name or not description:
            flash(gettext('You should fill both fields!'))
            return redirect(redirect_url())
        if groups.filter_by(name=name).count():
            flash(gettext('Group with this name already exist!'))
            return redirect(redirect_url())
        group = models.Group(name=name, description=description, pic='anon.jpg', owner=user.nickname,
                             date_create=datetime.datetime.utcnow())
        db.session.add(group)
        s = group.subscribe(user)
        if not s: db.session.add(s)
        db.session.commit()
        return redirect('/group/%s' % name)
    return render_template('groups.html', groups=groups, form=form, title='groups', nickname=session.get('nickname'))


@app.route('/group/<name>', defaults={'message_id': None}, methods=['POST', 'GET'])
@app.route('/group/<name>/add_comment/<int:message_id>', methods=['POST'])
@login_required
def group(name, message_id):
    group = models.Group.query.filter_by(name=name).first()
    if not group:
        flash(gettext('Group not found'))
        return redirect(redirect_url())
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    members = group.participants.all()
    subscription = user in members
    form = GroupSendMessage(prefix='form')
    if form.validate_on_submit():
        is_owner = form.owners_message.data
        msg_body = form.message_body.data
        msg_dest = name
        uploaded_files = request.files.getlist('form-message_file')
        if is_owner:
            msg_author = name
        else:
            msg_author = session.get('nickname')
        app.logger.info('msg_author is: %s' % msg_author)
        app.logger.info('type of: %s' % type(msg_author))
        try:
            message = core_api.add_message(msg_author=msg_author, msg_dest=msg_dest, msg_type='group',
                                           msg_body=msg_body,
                                           group_id=group.id, uploaded_files=uploaded_files)
        except (NoMessageBody, NoSuchUser, DestinationError):
            return redirect(redirect_url())

        return redirect(redirect_url() + '#%d' % message.msg_id)
    form2 = SendComment(prefix='form2')
    if form2.validate_on_submit():
        msg_author = user.nickname
        msg_dest = group.name
        msg_body = form2.comment_message_body.data
        message_file = form2.comment_message_file.data
        uploaded_files = flask.request.files.getlist('form2-comment_message_file') if message_file else None
        comment = _add_comment_to_message(message_id, msg_author, msg_body, uploaded_files)
        if not comment:
            return redirect(redirect_url())
        url = redirect_url() + '#%d' % comment.msg_id
        return redirect(url)
    owner = group.owner == user.nickname
    messages = models.Message.query.filter_by(msg_dest=name, msg_type='group')
    if group.tags:
        sub_messages = models.Message.query.filter(models.Message.tags.any(models.Tag.entity == group.tags[0].entity))
        for tag in group.tags[1:]:
            sub_messages = sub_messages.union(
                models.Message.query.filter(models.Message.tags.any(models.Tag.entity == tag.entity)))
        all_messages = messages.union(sub_messages).order_by(desc(models.Message.timestamp))
    else:
        all_messages = messages
    return render_template('group.html', owner=owner, group=group, members=members, subscription=subscription,
                           nickname=user.nickname, messages=all_messages, form=form, form2=form2, blog=True,
                           title=group.name)


@app.route('/sub_group/<name>', methods=['POST'])
@login_required
def sub_group(name):
    user = db.session.query(models.User).filter_by(nickname=session.get('nickname')).first()
    group = models.Group.query.filter_by(name=name).first()
    if not group:
        flash(gettext('Group not found'))
        return redirect(redirect_url())
    gr = group.subscribe(user)
    if not gr:
        flash(gettext('You have already subscribed'))
        return redirect(redirect_url())
    db.session.add(gr)
    db.session.commit()
    return redirect(redirect_url())


@app.route('/unsub_group/<name>', methods=['POST'])
@login_required
def unsub_group(name):
    user = models.User.query.filter_by(nickname=session.get('nickname')).first()
    group = models.Group.query.filter_by(name=name).first()
    if not group:
        flash(gettext('Group not found'))
        return redirect(redirect_url())
    gr = group.unsubscribe(user)
    if not gr:
        flash(gettext('You are not subscribed yet'))
        return redirect(redirect_url())
    db.session.add(gr)
    db.session.commit()
    return redirect(redirect_url())


@app.route('/edit_group/<name>', methods=['POST', 'GET'])
@login_required
def edit_group(name):
    user = models.User.query.filter_by(nickname=session.get('nickname')).first()
    group = models.Group.query.filter_by(name=name).first()
    if not group:
        flash(gettext('Group not found'))
        return redirect(redirect_url())
    if not group.owner == user.nickname:
        flash(gettext('Haxors not allowed!'))
        return redirect(redirect_url())
    form = GroupEdit()
    if form.validate_on_submit():
        tags = form.tags.data
        old_group_tags = [x.entity for x in group.tags]
        group.description = form.description.data
        if tags:
            tags, none = _truncate_tags(tags)
            for tag in tags:  # TODO: move it to model function with `update_tags` name
                if tag not in old_group_tags:
                    gr = group.subscribe_tag(models.Tag(entity=tag))
                    db.session.add(gr)
            for tag in old_group_tags:
                if tag not in tags:
                    gr = group.unsubscribe_tag(tag)
                    db.session.add(gr)
        if form.pic.data:
            filename = secure_filename(form.pic.data.filename)
            filename = datetime.datetime.utcnow().strftime('%y.%m.%d_%H:%M:%S_') + filename
            if not len(db.session.query(models.UploadedFile.filename).filter(
                            models.UploadedFile.filename == filename).all()):
                db.session.add(models.UploadedFile(file_author=user.nickname, filename=filename, \
                                                   upload_data=datetime.datetime.utcnow()))
                group.pic = filename
                form.pic.data.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                if utils.file_is_image(filename):
                    utils.save_thumb(filename)
        db.session.add(group)
        db.session.commit()
    else:  # fill fields
        form.description.data = group.description
        form.tags.data = ' '.join(['#' + x.entity for x in group.tags])
    return render_template('edit_group.html', form=form, group=group, user=user, nickname=user.nickname)
