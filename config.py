import os
import datetime
basedir = os.path.abspath(os.path.dirname(__file__))

#SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
DB_IP = os.environ.get('DB_IP') or '127.0.0.1'
DP_PORT = os.environ.get('DB_PORT') or '3306'  # default for mysql
SQLALCHEMY_DATABASE_URI = f'mysql://flask:difficult@{DB_IP}:{DB_PORT}/webportal?charset=utf8&use_unicode=1'
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
PATH_LOG_FILE = './logs/webportal.log'
LOG_FILE_SIZE = 1000*1000*100  # 100mb
CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'
UPLOAD_FOLDER = './user_upload/'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'pdf', 'flac', 'mp3', 'odt', 'zip', 'JPG', 'avi', 'mpg'])
TZ = 'Asia/Yekaterinburg'
TIMEOUT_CHAT = 1  # minutes
TIMEOUT_SOCIAL = 1  # minutes
REMEMBER_COOKIE_DURATION = datetime.timedelta(hours=30)
PERMANENT_SESSION_LIFETIME = datetime.timedelta(days=31)
BABEL_DEFAULT_LOCALE = 'en'
MYSQL_DATABASE_CHARSET='utf8'
DEFAULT_USERPIC = 'anon.jpg'  # NB: used in templates in hardcode manner
UPLOAD_THUMBS_FOLDER = './user_upload/thumbnails/'
RECAPTCHA_PUBLIC_KEY = '6LeYIbsSAAAAACRPIllxA7wvXjIE411PfdB2gt2J'
RECAPTCHA_PRIVATE_KEY = '6LeYIbsSAAAAAJezaIq3Ft_hSTo0YtyeFG-JgRtu'
COOKIE_EXPIRATION = 168  # hours
DEBUG_TB_INTERCEPT_REDIRECTS = False