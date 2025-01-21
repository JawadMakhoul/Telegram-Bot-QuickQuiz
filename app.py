from flask import Flask, request
import boto3
import requests
import random

# Initialize Flask app
app = Flask(__name__)

# AWS Resources
dynamodb = boto3.resource("dynamodb", region_name="us-west-1")  # Adjust region
quiz_table = dynamodb.Table("Quizzes")
user_table = dynamodb.Table("UserStates")

# Telegram API
TELEGRAM_TOKEN = "7467453386:AAEPsIImeqVnwNfeARnSU_WGeqMVtbTqRXM"
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/"

# AWS Translate
translate = boto3.client("translate")

def translate_text(text, target_language):
    response = translate.translate_text(
        Text=text, SourceLanguageCode="en", TargetLanguageCode=target_language
    )
    return response["TranslatedText"]

def get_user_language(user_id):
    response = user_table.get_item(Key={"UserID": str(user_id)})
    return response.get("Item", {}).get("Language", "en")

def get_random_quiz():
    response = quiz_table.scan(
        FilterExpression="Status = :status", ExpressionAttributeValues={":status": "Pending"}
    )
    quizzes = response["Items"]
    return random.choice(quizzes) if quizzes else None

def mark_quiz_as_sent(quiz_id):
    quiz_table.update_item(
        Key={"QuizID": quiz_id},
        UpdateExpression="SET Status = :status",
        ExpressionAttributeValues={":status": "Sent"},
    )

def send_message(chat_id, text):
    requests.get(BASE_URL + "sendMessage", params={"chat_id": chat_id, "text": text})

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"]["text"]

        if text.startswith("/setlanguage"):
            language_code = text.split()[1]
            supported_languages = ["en", "he", "ar"]
            if language_code not in supported_languages:
                send_message(chat_id, "Unsupported language. Use: en, he, ar.")
            else:
                user_table.update_item(
                    Key={"UserID": str(chat_id)},
                    UpdateExpression="SET Language = :lang",
                    ExpressionAttributeValues={":lang": language_code},
                )
                send_message(chat_id, f"Language set to {language_code}.")
        elif text == "/question":
            user_language = get_user_language(chat_id)
            quiz = get_random_quiz()
            if not quiz:
                send_message(chat_id, "All quizzes sent! Reset them to start again.")
            else:
                translated_question = translate_text(quiz["Question"], user_language)
                send_message(chat_id, f"Today's Quiz:\n{translated_question}")
                mark_quiz_as_sent(quiz["QuizID"])
        else:
            send_message(chat_id, "Unknown command. Use /setlanguage or /question.")

    return "OK", 200