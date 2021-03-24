import os

from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from teleflask import Teleflask
from teleflask.messages import TextMessage

TOKEN = os.environ['TELEGRAM_TOKEN']
OWNER_CHAT_ID = os.environ['OWNER_CHAT_ID']

app = Flask(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
bot = Teleflask(TOKEN, app)


@app.route('/', methods=['GET'])
def hello_world():
    return "index"


# Register the /start command
@bot.command("start")
def start(update, text):
    # update is the update object. It is of type pytgbot.api_types.receivable.updates.Update
    # text is the text after the command. Can be empty. Type is str.
    return TextMessage("<b>Hello!</b> Thanks for using @" + bot.username + "!",
                       parse_mode="html")
