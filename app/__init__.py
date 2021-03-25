import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

TOKEN = os.environ['TELEGRAM_TOKEN']
URI = "/{}".format(TOKEN.replace(':', '-'))
OWNER_CHAT_ID = os.environ['OWNER_CHAT_ID']
BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)
SEND_MESSAGE_URL = BASE_URL + "/sendMessage"

app = Flask(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.route('/', methods=['GET'])
def hello_world():
    return "index"


@app.route(URI, methods=['GET'])
def hello_world():
    return "index"
