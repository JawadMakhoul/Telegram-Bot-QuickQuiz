import json
from helpers import send_daily_quiz, handle_set_language, send_message

def lambda_handler(event, context):
    body = json.loads(event.get("body", "{}"))
    if "message" in body:
        chat_id = body["message"]["chat"]["id"]
        text = body["message"]["text"]

        if text.startswith("/setlanguage"):
            language_code = text.split()[1]
            response = handle_set_language(chat_id, language_code)
        elif text == "/question":
            response = send_daily_quiz(chat_id)
        else:
            response = "Unknown command. Use /setlanguage or /question."

        send_message(chat_id, response)

    return {"statusCode": 200, "body": "OK"}