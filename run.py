#!usr/bin/python
from app import app
from flask_debugtoolbar import DebugToolbarExtension
from flask_debugtoolbar_lineprofilerpanel.profile import line_profile
import logging
from logging.handlers import RotatingFileHandler
import os

app.debug = True # for uwsgi
handler = RotatingFileHandler('/home/je/flask.log', maxBytes=1000000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
os.environ['LANG'] = 'en_US.UTF-8'
os.environ['LC_CTYPE'] = 'en_US.UTF-8'

if __name__ == '__main__':
    toolbar = DebugToolbarExtension(app)
    app.config['DEBUG_TB_PANELS'] = [
        'flask_debugtoolbar.panels.versions.VersionDebugPanel',
        'flask_debugtoolbar.panels.timer.TimerDebugPanel',
        'flask_debugtoolbar.panels.headers.HeaderDebugPanel',
        'flask_debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
        'flask_debugtoolbar.panels.template.TemplateDebugPanel',
        'flask_debugtoolbar.panels.sqlalchemy.SQLAlchemyDebugPanel',
        'flask_debugtoolbar.panels.logger.LoggingPanel',
        'flask_debugtoolbar.panels.profiler.ProfilerDebugPanel',
        # Add the line profiling
        'flask_debugtoolbar_lineprofilerpanel.panels.LineProfilerPanel'
    ]
    app.run(debug = True, host = '0.0.0.0')
