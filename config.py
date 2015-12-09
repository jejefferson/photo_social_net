import os
import datetime
basedir = os.path.abspath(os.path.dirname(__file__))

#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_DATABASE_URI = 'mysql://flask:difficult@localhost/webportal?charset=utf8&use_unicode=0'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'
UPLOAD_FOLDER = '/home/je/programming/flask/app/upload'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'pdf', 'flac', 'mp3', 'odt', 'zip', 'JPG', 'avi', 'mpg'])
TZ = 'Asia/Yekaterinburg'
TIMEOUT_CHAT = 1 #minutes
TIMEOUT_SOCIAL = 1 #minutes
REMEMBER_COOKIE_DURATION = datetime.timedelta(hours=30)
PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=31)
BABEL_DEFAULT_LOCALE = 'en'
MYSQL_DATABASE_CHARSET='utf8'
DEFAULT_USERPIC = 'anon.jpg' #must locate in /upload and /upload/thumbnails folders
UPLOAD_THUMBS_FOLDER = '/home/je/programming/flask/app/upload/thumbnails'
RECAPTCHA_PUBLIC_KEY = '6LeYIbsSAAAAACRPIllxA7wvXjIE411PfdB2gt2J'
RECAPTCHA_PRIVATE_KEY = '6LeYIbsSAAAAAJezaIq3Ft_hSTo0YtyeFG-JgRtu'
COOKIE_EXPIRATION = 168 #hours
