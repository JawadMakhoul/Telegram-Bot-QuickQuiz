from flask import Flask, request, jsonify, Response
import requests
from dynamodb_connect import connect_to_dynamodb_quizTable, connect_to_dynamodb_userLastQuizTable, connect_to_dynamodb_chatIDsTable # Your existing file to connect to DynamoDB
from apscheduler.schedulers.background import BackgroundScheduler
import random
import emoji
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
app = Flask(__name__)

TOKEN = '7467453386:AAEPsIImeqVnwNfeARnSU_WGeqMVtbTqRXM'
SUB_TOKEN = TOKEN[8:54]
TELEGRAM_INIT_WEBHOOK_URL = 'https://api.telegram.org/bot{}/setWebhook?url=https://8252-2a06-c701-7a9c-3e00-cc5-3b2-1c73-7e42.ngrok-free.app/message'.format(SUB_TOKEN)
requests.get(TELEGRAM_INIT_WEBHOOK_URL)

user_last_quiz = {}
quiz_table = connect_to_dynamodb_quizTable()
user_last_quiz = connect_to_dynamodb_userLastQuizTable()  # Connect to the Quiz table
chat_ids_table = connect_to_dynamodb_chatIDsTable()

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
    return secret

@app.route('/message', methods=['GET', 'POST'])
def handle_message():

    if request.method == 'POST':
        data = request.get_json()

        # Debug log to inspect incoming data
        print(f"Incoming update: {data}")

        # Check if the update is a callback query
        if 'callback_query' in data:
            callback_query = data['callback_query']
            chat_id = callback_query['message']['chat']['id']
            callback_data = callback_query['data']
            print(f"Callback query from chat_id {chat_id} with data: {callback_data}")

            if callback_data == '/getAnswer':
                answer = get_last_quiz_answer(chat_id)
                send_telegram_message(chat_id, answer)

            elif callback_data == '/getWelcomingAnswer':
                send_telegram_message(chat_id, "The answer to your last quiz is: 8")

            # Acknowledge the callback query
            callback_id = callback_query['id']
            url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
            response = requests.post(url, json={"callback_query_id": callback_id})
            if response.status_code != 200:
                print(f"Failed to acknowledge callback query: {response.text}")
            else:
                print(f"Callback query acknowledged successfully: {response.text}")

            return Response("success", status=200)

        # Handle regular messages
        if 'message' in data:
            chat_id = data['message']['chat']['id']
            text = data['message'].get('text', '').strip().lower()

            if text == '/start':
                add_chat_id(chat_id)
                send_animation(chat_id, get_random_gif(WELCOME_GIFS))
                send_telegram_message(chat_id, "Hello! Welcome to the bot. You'll receive a quiz daily!\n Be ready for the welcoming quiz \U0001F603")
                send_welcome_quiz(chat_id)
               
            elif text == '/getAnswer':
                answer = get_last_quiz_answer(chat_id)
                send_telegram_message(chat_id, answer)
            
            elif text == '/exit':
                send_animation(chat_id, get_random_gif(GOODBYE_GIFS))
                send_telegram_message(chat_id, "Farewell! You'll always be welcome here. ❤️")
                remove_chat_id(chat_id)
        
            else:
                result = process_user_answer(chat_id, text)
                send_telegram_message(chat_id, result)

            return Response("success", status=200)

        return Response("Invalid request", status=400)
    else:
        return Response("GET method not allowed", status=405)

def send_welcome_quiz(chat_id):
    """
    Send a predefined welcoming quiz to the user.
    """
    try:
        # Define the fixed welcome quiz
        welcome_quiz_question = "What is the result of 2³ (2 raised to the power of 3)?"
        welcome_quiz_answer = "8"

        
        # Send the welcoming quiz question
        send_telegram_message(
            chat_id,
            f"Welcoming Quiz: {welcome_quiz_question}\n\nIf you ever feel like leaving the bot, you can click on /exit. We'll miss you dearly. 😢",
            include_get_welcoming_answer_button=True
        )

        # Track the quiz_id as "welcome" in the user's data
        user_last_quiz.put_item(Item={"chat_id": str(chat_id), "quiz_id": str(0)})

    except Exception as e:
        print(f"Error sending welcome quiz: {str(e)}")

CORRECT_ANSWER_GIFS = [
    "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzhvenJuOHVrMWJ1ZHh4NnVxYnI1OXo4cGYzdjdobzk3ZnBzMmdtaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/3rYxjPwF5i9mALN1UM/giphy.gif",
    "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExYndxaXdkZmJ2MGdsZTdkaDI4ZG5zaDJ0ZWw4anVwN2Ywb3JsNm0xayZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/5R2YzhtLB1Q7Nf6dyl/giphy.gif",
    "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExbjBuMWtrMjJjYzIxeXFtdXpudThtbXMyZDBkYng0cThnMWcyaWI5aSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/YrMpuzXd1aro5pAHiV/giphy.gif",
    "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExbG41M2xzM29rbGh1c250em16c25xc3l1dDByMmplZnR4aDN6eW45eSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9dg/aG2csyWgGANQsgoeyJ/giphy.gif",
    "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExenR6eGZtZHFjem1ta2pqZ2V5bGp5ZG9oMjVvbmJ3eWxyMW9yZmxzeCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/STqvaWDhEm5PvwBVat/giphy.gif",
    "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExbjhocHlnaHU3Y2FuM3Jyd3VmNWM4anRrYnc1bDV3dDRma2xoMG5jcSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/E1np7OHl4btmT7aVEO/giphy.gif",
    "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExb3RmMnVwd2V1a3J6d3I3YThnY3J3bnRpczB1ZmlmZWg5YXA5bDNjeCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/cegQmGA1XcNH13Zrx7/giphy.gif"

]   

WRONG_ANSWER_GIFS = [
    "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExa2d1ZjN0aHp0OHYyZWJnYmt0cjF0ZDI2dnRmcGs5cGtqYmNqZnA2MyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/dYrihH20uiozcPFq4E/giphy.gif",
    "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExYm1ueTV4c2tpcWFpcDRyZ25wZDlkdml1YXZxOGVvYTBycTRlNGV0dSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/fsW9ukNzT99V5TzTx8/giphy.gif",
    "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExcjhoOHZldGNhcmFnc2QzdGI0YTZnb2Y4cTIzaWF6ZDd3cGgxN2ZwYiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/J4nRh9e7Xrv7D81tvG/giphy.gif",
    "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExcjhoOHZldGNhcmFnc2QzdGI0YTZnb2Y4cTIzaWF6ZDd3cGgxN2ZwYiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/J4nRh9e7Xrv7D81tvG/giphy.gif",
    "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExYXVkOHdtd2VkeTJxcTVvZWM3NzBudG82Zm8zMmhwNjFieG82NGxmOCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/VJGoS8mjnpHFhAdJiH/giphy.gif",
    "https://media3.giphy.com/media/v1.Y2lkPTc5MGI3NjExMTJqeHFjY3UxNWE1d2s0eHd5enNvOGNscWVwNmd4dTBsbDlsNWJqYiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/NEMM40tpnV6KhMHdZD/giphy.gif",
    "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExMHoyMWtqYXp6dHAwNDBhemN6NGxvYnozNDI2OHUya2J3bHJzcXBpcCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/Qv4Fc784YycPcNpy6O/giphy.gif",
    "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExNzNvamNpZDZsNmxzbjRkNmJpdm5mcjd4ZTcxcW11ZHFjMWVhN2xkdCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/qi5W1VbipdQPiUnvE8/giphy.gif"
]

GOODBYE_GIFS = [
    "https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExNTBxbmhrZDlvenpucHBnbGlua2QxYWw1aGs0cTY4MXA4cWQzeDA4MCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/UQaRUOLveyjNC/giphy.gif",
    "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExOHkxa256OHd5bjhoOWxycHdjYjh4bHUyY2E5OTJleG0zeWR0bmw2NiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xUPGcGyYhQTYtDtwBy/giphy.gif",
    "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExODE1M2p0emM2Zm10OGlsanZsN3dzMXlrOGVtdjk5MmZxb2F6cjhobSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/UWmVAwlUI2MFOGANDA/giphy.gif",
    "https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExYWYzOWFlNnFhZnM3dmpzcTZpdGNodjgwYzYzc2s3cXAxNGwwZW5jbyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/12noFudALzfIynHuUp/giphy.gif"
]

WELCOME_GIFS = [
    "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExZXdyemRtZTV2YWhkcnNyZ3Y5Y2U4YWc3aDR6azZhZmw4MXRhNzg0aiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/mCbUi0FyYhHHhutEV8/giphy.gif",
    "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExY212Yng4cDAzd2JtYjM2amtzc3ozNWQ3bXIyNnR6cnVhc3o5Mmc1ZSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/ggtpYV17RP9lTbc542/giphy.gif",
    "https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExa2hrb2ZnNWx1dHA1ZmN2ZnprajlpYXVxN2ZrcGN3ZWxkYTR2M3lhNCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l4JyOCNEfXvVYEqB2/giphy.gif"
]

def get_random_gif(gif_list):
    return random.choice(gif_list)

def send_animation(chat_id, animation_url):
    """
    Send an animation (GIF) to the Telegram user.
    """
    url = f"https://api.telegram.org/bot{TOKEN}/sendAnimation"
    payload = {
        "chat_id": chat_id,
        "animation": animation_url
    }
    response = requests.post(url, data=payload)

    if response.status_code != 200:
        print(f"Failed to send animation: {response.text}")
    else:
        print(f"Animation sent to chat_id {chat_id}")


def process_user_answer(chat_id, user_answer):
    """
    Process the user's answer, check it against the correct answer, and return the result.
    """
    try:
        # Get the last quiz_id for the user
        response = user_last_quiz.get_item(Key={"chat_id": str(chat_id)})
        user_data = response.get('Item', {})

        if not user_data:
            return "No quiz has been sent to you yet. Please wait for the next quiz."

        # Fetch the correct answer from DynamoDB
        quiz_id = user_data.get('quiz_id')
        if quiz_id == "0":
            correct_answer = "8"  # Predefined answer for the welcome quiz
            if check_answer(user_answer, correct_answer):
                send_animation(chat_id, get_random_gif(CORRECT_ANSWER_GIFS))
                return "Correct! Well done! Please wait for tomorrow's quiz!"
            else:
                send_animation(chat_id, get_random_gif(WRONG_ANSWER_GIFS))
                send_telegram_message(
                chat_id,
                "You can try again or click the button below to see the correct answer.",
                include_get_welcoming_answer_button=True
            )
            return None
        quiz_data = quiz_table.get_item(Key={"quiz_id": str(quiz_id)}).get('Item', {})

        if not quiz_data:
            return "Unable to retrieve the quiz question. Please try again later."

        correct_answer = quiz_data.get('answer', 'No answer available.')
        # Check the user's answer
        if check_answer(user_answer, correct_answer):
            # Send a celebratory animation if the answer is correct
            
            send_animation(chat_id, get_random_gif(CORRECT_ANSWER_GIFS))
            return "Correct! Well done! Please wait for tomorrow's quiz!"
        else:
            send_animation(chat_id, get_random_gif(WRONG_ANSWER_GIFS))
            send_telegram_message(
                chat_id,
                "You can try again or click the button below to see the correct answer.",
                include_get_answer_button=True
            )
            return None
    except Exception as e:
        print(f"Error processing user answer: {str(e)}")
        return "An error occurred while processing your answer. Please try again."
    

    
def check_answer(user_answer, correct_answer):
    """
    Check if the user's answer matches the correct answer.
    This comparison is case-insensitive and ignores extra spaces.
    """
    # Normalize both answers by converting to lowercase and stripping spaces
    normalized_user_answer = " ".join(user_answer.lower().split())
    normalized_correct_answer = " ".join(correct_answer.lower().split())

    # Compare the normalized answers
    return normalized_user_answer == normalized_correct_answer

def send_daily_quiz():
    """
    Send the same random daily quiz to all users and update the last sent quiz ID for each user.
    """
    try:
        # Fetch all quizzes from DynamoDB
        response = quiz_table.scan()
        all_quizzes = response.get('Items', [])
        
        if not all_quizzes:
            print("No quizzes available in the database.")
            return

        # Select a random quiz for today
        random_quiz = random.choice(all_quizzes)
        quiz_id = random_quiz['quiz_id']
        question = random_quiz['question']
        
        # Fetch all chat IDs
        all_chat_ids = fetch_all_chat_ids()

        for chat_id in all_chat_ids:
            # Send the quiz to the user
            send_telegram_message(chat_id, f"Today's Quiz: {question} \n\nIf you ever feel like leaving the bot, you can click on /exit. We'll miss you dearly. 😢", include_get_answer_button=True)
            
            # Update the user's last sent quiz ID in the database
            user_last_quiz.put_item(Item={"chat_id": chat_id, "quiz_id": str(quiz_id)})

        print(f"Quiz ID {quiz_id} has been sent to all users.")
    
    except Exception as e:
        print(f"Error sending daily quiz: {str(e)}")

def get_last_quiz_answer(chat_id):
    """
    Fetch the answer for the last quiz sent to a specific user.
    """
    try:
        # Get the last quiz_id for the user
        response = user_last_quiz.get_item(Key={"chat_id": str(chat_id)})
        user_data = response.get('Item', {})
        
        if not user_data:
            return "No quiz has been sent to you yet. Please wait for the next quiz."
       
        # Fetch the quiz from DynamoDB
        quiz_id = user_data.get('quiz_id')
        quiz_data = quiz_table.get_item(Key={"quiz_id": str(quiz_id)}).get('Item', {})
        
        if quiz_data:
            return f"The answer to your last quiz is: {quiz_data.get('answer', 'No answer available.')}"
        else:
            return "Unable to retrieve the quiz answer."
    except Exception as e:
        print(f"Error fetching last quiz answer: {str(e)}")
        return "There was an error fetching the answer. Please try again later."

def add_chat_id(chat_id):
    """
    Add a chat ID to the UserChatIDs table if it doesn't already exist.
    """
    try:
        response = chat_ids_table.get_item(Key={"chat_id": str(chat_id)})
        if 'Item' not in response:
            chat_ids_table.put_item(Item={"chat_id": str(chat_id)})
            print(f"Chat ID {chat_id} added to the database.")
        else:
            print(f"Chat ID {chat_id} already exists.")
    except Exception as e:
        print(f"Error adding chat ID: {str(e)}")

def remove_chat_id(chat_id):
    """
    Remove a chat ID from the UserChatIDs table.
    """
    try:
        response = chat_ids_table.delete_item(
            Key={"chat_id": str(chat_id)}
        )

        response = user_last_quiz.delete_item(
            Key={"chat_id": str(chat_id)}
        )
        print(f"Chat ID {chat_id} removed from the database.")
    except Exception as e:
        print(f"Error removing chat ID: {str(e)}")

def fetch_all_chat_ids():
    """
    Retrieve all chat IDs for broadcasting quizzes from the UserChatIDs table.
    """
    try:
        response = chat_ids_table.scan()
        chat_ids = [item['chat_id'] for item in response.get('Items', [])]
        return chat_ids
    except Exception as e:
        print(f"Error fetching chat IDs: {str(e)}")
        return []

def send_telegram_message(chat_id, text,include_get_answer_button=False, include_get_welcoming_answer_button=False):
    """
    Send a message to the Telegram user.
    """
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
    }

    if include_get_answer_button:
        # Add an inline keyboard with a /getAnswer button
        reply_markup = '{"inline_keyboard": [[{"text": "Get Answer", "callback_data": "/getAnswer"}]]}'
        payload['reply_markup'] = reply_markup  # Send as a string

    elif include_get_welcoming_answer_button:
        # Add an inline keyboard with a /getAnswer button
        reply_markup = '{"inline_keyboard": [[{"text": "Get Answer", "callback_data": "/getWelcomingAnswer"}]]}'
        payload['reply_markup'] = reply_markup  # Send as a string

    response = requests.post(url, data=payload)
    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")
    else:
        print(f"Message sent to chat_id {chat_id}: {text}")

# Initialize APScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_quiz, 'cron', hour=16, minute=38)  # Schedule at 9:00 AM daily
scheduler.start()

if __name__ == '__main__':
    app.run(port=5002)
