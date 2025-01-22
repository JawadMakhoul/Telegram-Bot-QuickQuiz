import boto3
import json
import requests
from datetime import datetime
from botocore.exceptions import ClientError


# DynamoDB table name
QUIZ_TABLE = "Quiz"

# DynamoDB Client
dynamodb = boto3.resource('dynamodb')
quiz_table = dynamodb.Table(QUIZ_TABLE)

def lambda_handler(event, context):
    # Parse incoming webhook from Telegram
    body = json.loads(event['body'])
    chat_id = body['message']['chat']['id']
    command = body['message']['text']

    if command == "/start":
        return send_message(chat_id, "Welcome to the daily quiz bot!")
    elif command == "/getAnswer":
        return send_last_answer(chat_id)
    else:
        return send_message(chat_id, "Unknown command. Use /getAnswer or wait for tomorrow's quiz.")

def send_last_answer(chat_id):
    # Fetch today's quiz ID
    today = datetime.now().date()
    quiz_id = str(today.toordinal())  # Use today's ordinal date as quiz_id
    quiz_data = quiz_table.get_item(Key={"quiz_id": quiz_id}).get('Item', {})

    if not quiz_data:
        return send_message(chat_id, "No quiz available for today. Check back tomorrow!")

    answer = quiz_data.get("answer", "No answer available.")
    return send_message(chat_id, f"The answer to today's quiz is: {answer}")

def send_message(chat_id, text):
    # Get bot token from Secrets Manager
    secrets_client = boto3.client("secretsmanager")
    secret = secrets_client.get_secret_value(SecretId=get_secret())
    bot_token = json.loads(secret["SecretString"])["BOT_TOKEN"]

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    response = requests.post(url, json=payload)
    return {"statusCode": 200, "body": json.dumps(response.json())}

def send_daily_quiz(event, context):
    # Fetch today's quiz
    today = datetime.now().date()
    quiz_id = str(today.toordinal())  # Use today's ordinal date as quiz_id
    quiz_data = quiz_table.get_item(Key={"quiz_id": quiz_id}).get('Item', {})

    if not quiz_data:
        return {"statusCode": 200, "body": "No quiz available for today."}

    question = quiz_data['question']
    #users = get_all_users_from_telegram()  # Implement logic to fetch all users.

    # Send the quiz to all users
    #for user in users:
    #    send_message(user, f"Today's Quiz: {question}")

    #return {"statusCode": 200, "body": "Quiz sent to all users."}



def get_secret():

    secret_name = "BotToken"
    region_name = "us-east-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']
    print(secret)
    return secret