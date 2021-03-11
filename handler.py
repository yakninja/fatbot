import json
import os

import requests

# here = os.path.dirname(os.path.realpath(__file__))
# sys.path.append(os.path.join(here, "./vendored"))

TOKEN = os.environ['TELEGRAM_TOKEN']
BASE_URL = "https://api.telegram.org/bot{}".format(TOKEN)
SEND_MESSAGE_URL = BASE_URL + "/sendMessage"


def webhook(event, context):
    """
    This is where we get an event once someone sends a message to the bot.
    We ignore everything they've said and just reply with a generated text message
    :param event:
    :param context:
    :return:
    """
    try:
        data = json.loads(event["body"])
        message = str(data["message"]["text"])  # yes, ignore this
        chat_id = data["message"]["chat"]["id"]
        first_name = data["message"]["chat"]["first_name"]

        response = '{}'.format(first_name)

        data = {"text": response.encode("utf8"), "chat_id": chat_id}
        requests.post(SEND_MESSAGE_URL, data)

    except Exception as e:
        pass

    return {"statusCode": 200}
