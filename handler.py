import json
import os

import requests

# here = os.path.dirname(os.path.realpath(__file__))
# sys.path.append(os.path.join(here, "./vendored"))

TOKEN = os.environ['TELEGRAM_TOKEN']
OWNER_CHAT_ID = os.environ['OWNER_CHAT_ID']

BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)
SEND_MESSAGE_URL = BASE_URL + "/sendMessage"


def webhook(event, context):
    """
    This is where we get an event once someone sends a message to the bot
    :param event:
    :param context:
    :return:
    """
    try:
        data = json.loads(event["body"])
        message = str(data["message"]["text"])
        chat_id = data["message"]["chat"]["id"]
        first_name = data["message"]["chat"]["first_name"]

        response = 'Принял: "{}"'.format(message)
        data = {"text": response.encode("utf8"), "chat_id": chat_id}
        requests.post(SEND_MESSAGE_URL, data)

        response = '{}'.format(message)
        data = {"text": response.encode("utf8"), "chat_id": OWNER_CHAT_ID}
        requests.post(SEND_MESSAGE_URL, data)

    except Exception as e:
        pass

    return {"statusCode": 200}
