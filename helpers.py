import boto3
import requests
import random

# AWS Resources
dynamodb = boto3.resource("dynamodb", region_name="us-west-1")  # Adjust region
quiz_table = dynamodb.Table("Quizzes")
user_table = dynamodb.Table("UserStates")

# AWS Translate
translate = boto3.client("translate")

# Telegram API
TELEGRAM_TOKEN = "7467453386:AAEPsIImeqVnwNfeARnSU_WGeqMVtbTqRXM"
BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/"

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

def handle_set_language(user_id, language_code):
    supported_languages = ["en", "he", "ar"]
    if language_code not in supported_languages:
        return "Unsupported language. Use: en, he, ar."

    user_table.update_item(
        Key={"UserID": str(user_id)},
        UpdateExpression="SET Language = :lang",
        ExpressionAttributeValues={":lang": language_code},
    )
    return f"Language set to {language_code}."

def send_daily_quiz(user_id):
    user_language = get_user_language(user_id)
    quiz = get_random_quiz()
    if not quiz:
        return "All quizzes have been sent! Reset them to start again."

    translated_question = translate_text(quiz["Question"], user_language)
    send_message(user_id, f"Today's Quiz:\n{translated_question}")
    mark_quiz_as_sent(quiz["QuizID"])
    return "Quiz sent successfully!"