import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import json
import requests
from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from dynamodb_connect import connect_to_dynamodb  # Use your existing DynamoDB connection file

# Create Flask app instance
app = Flask(__name__)

# Connect to DynamoDB Quiz table
quiz_table = connect_to_dynamodb()

@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Handle incoming Telegram webhook requests.
    """
    data = request.get_json()

    # Validate the request
    if not data or 'message' not in data:
        return jsonify({"error": "Invalid request"}), 400

    # Extract message details
    chat_id = data['message']['chat']['id']
    text = data['message']['text']

    # Handle commands
    if text == "/start":
        send_message(chat_id, "Welcome to the daily quiz bot! You'll receive a daily quiz.")
    elif text == "/getAnswer":
        answer = get_last_answer()
        send_message(chat_id, answer)
    else:
        send_message(chat_id, "Unknown command. Use /getAnswer or wait for tomorrow's quiz.")

    return jsonify({"status": "success"}), 200


def get_last_answer():
    """
    Fetch the last quiz answer.
    """
    yesterday = datetime.now().date() - timedelta(days=1)
    quiz_id = str(yesterday.toordinal())  # Yesterday's quiz ID

    try:
        quiz_data = quiz_table.get_item(Key={"quiz_id": quiz_id}).get('Item', {})
        return quiz_data.get("answer", "No answer available for the last quiz.")
    except Exception as e:
        return f"Error fetching answer: {str(e)}"


def send_daily_quiz():
    """
    Send the daily quiz to all users.
    """
    today = datetime.now().date()
    quiz_id = str(today.toordinal())  # Today's quiz ID

    # Fetch today's quiz
    try:
        quiz_data = quiz_table.get_item(Key={"quiz_id": quiz_id}).get('Item', {})
        question = quiz_data.get("question", "No quiz available for today.")
    except Exception as e:
        print(f"Error fetching today's quiz: {str(e)}")
        return

    # Replace this with your method to manage chat IDs
    all_chat_ids = fetch_all_chat_ids()

    for chat_id in all_chat_ids:
        send_message(chat_id, f"Today's Quiz: {question}")


def fetch_all_chat_ids():
    """
    Retrieve all chat IDs for broadcasting quizzes.
    """
    # Replace this logic with a proper method to retrieve chat IDs (e.g., a file or memory store)
    return ["123456789", "987654321"]  # Example static IDs


def send_message(chat_id, text):
    """
    Send a message to a Telegram user.
    """
    bot_token = get_secret()
    sub_token = bot_token[8:54]
    url = f"https://api.telegram.org/bot{sub_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload)
    return response.json()


def get_secret():
    """
    Retrieve the Telegram bot token from AWS Secrets Manager.
    """
    secret_name = "BotToken"
    region_name = "us-east-1"
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        return get_secret_value_response['SecretString']
    except ClientError as e:
        raise e

# Schedule the daily quiz
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_quiz, 'cron', hour=9, minute=0)  # Adjust time as needed
scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=443)