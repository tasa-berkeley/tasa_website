import os
import string
import sqlite3
import yaml

from contextlib import closing
from flask import Flask
from flask import g

# configuration
CWD = os.getcwd()
ROOT = 'tasa_website/'
DATABASE = 'tasa_website/tasa_website.db'
CONFIG = 'tasa_website/config.yaml'
DEBUG = True
IMAGE_FOLDER = 'static/images/events/'
OFFICER_IMAGE_FOLDER = 'static/images/officers/'
FAMILY_IMAGE_FOLDER = 'static/images/families/'
FILES_FOLDER = 'static/files/'

secrets = {}
with open(CONFIG, 'r') as config:
    secrets = yaml.load(config)

SECRET_KEY = secrets['secret']

app = Flask(__name__)
app.config.from_object(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16 megabytes

def connect_db():
    return sqlite3.connect(app.config['DATABASE'])

def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()

@app.before_request
def before_request():
    g.db = connect_db()
    g.db.row_factory = sqlite3.Row

@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = cur.fetchall()
    g.db.commit()
    cur.close()
    return (rv[0] if rv else None) if one else rv

# This is really ugly, but allows us to use decorators in views.py
# See http://flask.pocoo.org/docs/0.12/patterns/packages/
import tasa_website.views
import tasa_website.auth
