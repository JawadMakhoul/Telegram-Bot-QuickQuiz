import boto3
import json
import requests
from datetime import datetime
from botocore.exceptions import ClientError

# DynamoDB table name
QUIZ_TABLE = "Quiz"

# DynamoDB Client
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  
quiz_table = dynamodb.Table(QUIZ_TABLE)


def main():
    print("Starting the bot...")
    # Simulating receiving commands from Telegram
    while True:
        print("Waiting for a command...")
        # Replace this section with the logic to fetch commands from Telegram webhook or polling
        command = input("Enter a command (/start or /getAnswer): ").strip()

        if command == "/start":
            print(send_message("Welcome to the daily quiz bot!"))
        elif command == "/getAnswer":
            print(send_last_answer())
        else:
            print("Unknown command. Use /getAnswer or wait for tomorrow's quiz.")


def send_last_answer():
    # Fetch today's quiz ID
    today = datetime.now().date()
    quiz_id = str(today.toordinal())  # Use today's ordinal date as quiz_id
    quiz_data = quiz_table.get_item(Key={"quiz_id": quiz_id}).get('Item', {})

    if not quiz_data:
        return "No quiz available for today. Check back tomorrow!"

    answer = quiz_data.get("answer", "No answer available.")
    return f"The answer to today's quiz is: {answer}"


def send_message(event):
    # Get bot token from Secrets Manager
    bot_token = get_secret()
    sub_token = bot_token[8:54]

    # Extract chat_id from the event (user's message)
    body = json.loads(event['body'])
    chat_id = body['message']['chat']['id']
    text = "Welcome! This is a dynamic message."

    # Construct the Telegram API URL and payload
    url = f"https://api.telegram.org/bot{sub_token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}

    # Send the message
    response = requests.post(url, json=payload)
    return response.json()


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

    return get_secret_value_response['SecretString']        


if __name__ == "__main__":
    main()