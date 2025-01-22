from flask import Flask, request
from helpers import send_daily_quiz, handle_set_language, send_message

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]

        if text.startswith("/setlanguage"):
            language_code = text.split()[1]
            response = handle_set_language(chat_id, language_code)
        elif text == "/question":
            response = send_daily_quiz(chat_id)
        else:
            response = "Unknown command. Use /setlanguage or /question."

        send_message(chat_id, response)

    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)