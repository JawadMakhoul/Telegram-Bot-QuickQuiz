from flask import Flask, request, jsonify, Response
import requests
from dynamodb_connect import connect_to_dynamodb_quizTable, connect_to_dynamodb_userLastQuizTable, connect_to_dynamodb_chatIDsTable # Your existing file to connect to DynamoDB
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

TOKEN = '7467453386:AAEPsIImeqVnwNfeARnSU_WGeqMVtbTqRXM'
TELEGRAM_INIT_WEBHOOK_URL = 'https://api.telegram.org/bot{}/setWebhook?url=https://8252-2a06-c701-7a9c-3e00-cc5-3b2-1c73-7e42.ngrok-free.app/message'.format(TOKEN)
requests.get(TELEGRAM_INIT_WEBHOOK_URL)

user_last_quiz = {}
quiz_table = connect_to_dynamodb_quizTable()
user_last_quiz = connect_to_dynamodb_userLastQuizTable()  # Connect to the Quiz table
chat_ids_table = connect_to_dynamodb_chatIDsTable()


@app.route('/message', methods=['GET', 'POST'])
def handle_message():
    if request.method == 'POST':
        data = request.get_json()

        # Validate incoming data
        if not data or 'message' not in data:
            return Response("Invalid request", status=400)

        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '').strip().lower()

        # Handle /start command
        if text == '/start':
            add_chat_id(chat_id)
            send_telegram_message(chat_id, "Hello! Welcome to the bot. You'll receive a quiz daily!")
        # Handle /getAnswer command
        elif text == '/getanswer':
            answer = get_last_quiz_answer(chat_id)
            send_telegram_message(chat_id, answer)
        else:
            result = process_user_answer(chat_id, text)
            send_telegram_message(chat_id, result)

        return Response("success", status=200)
    else:
        return Response("GET method not allowed", status=405)

@app.route('/callback', methods=['POST'])
def handle_callback_query():
    """
    Handle inline button callbacks (e.g., /getAnswer button).
    """
    data = request.get_json()
    print(f"Callback data received: {data}")  # Log the full callback query

    if 'callback_query' in data:
        callback_query = data['callback_query']
        chat_id = callback_query['message']['chat']['id']
        callback_data = callback_query['data']
        print(f"Chat ID: {chat_id}, Callback Data: {callback_data}")  # Log the extracted information

        if callback_data == "/getAnswer":
            answer = get_last_quiz_answer(chat_id)
            send_telegram_message(chat_id, answer)

        # Respond to Telegram to acknowledge the callback
        callback_id = callback_query['id']
        url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
        response = requests.post(url, json={"callback_query_id": callback_id})
        print(f"Callback acknowledgment response: {response.text}")  # Debug acknowledgment

    return Response("success", status=200)

def send_animation(chat_id, animation_url):
    """
    Send an animation (GIF) to the Telegram user.
    """
    url = f"https://api.telegram.org/bot{TOKEN}/sendAnimation"
    payload = {
        "chat_id": chat_id,
        "animation": animation_url
    }
    response = requests.post(url, json=payload)

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
        quiz_data = quiz_table.get_item(Key={"quiz_id": str(quiz_id)}).get('Item', {})

        if not quiz_data:
            return "Unable to retrieve the quiz question. Please try again later."

        correct_answer = quiz_data.get('answer', 'No answer available.')
        # Check the user's answer
        if check_answer(user_answer, correct_answer):
            # Send a celebratory animation if the answer is correct
            animation_url = "https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzhvenJuOHVrMWJ1ZHh4NnVxYnI1OXo4cGYzdjdobzk3ZnBzMmdtaCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/3rYxjPwF5i9mALN1UM/giphy.gif"  # Replace with your GIF URL
            send_animation(chat_id, animation_url)
            return "Correct! Well done! Please wait for tomorrow's quiz!"
        else:
            send_telegram_message(
                chat_id,
                "Incorrect! You can try again or click the button below to see the correct answer.",
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
    Send the daily quiz to all users and store the quiz_id for each user.
    """
    try:
        
        # Fetch the latest quiz from DynamoDB (you can adjust the logic as needed)
        response = quiz_table.scan(Limit=1)  # Assume the latest quiz is the first item
        quiz_data = response['Items'][0] if response['Items'] else None
        
        if not quiz_data:
            print("No quiz available to send.")
            return
        
        quiz_id = quiz_data['quiz_id']
        question = quiz_data['question']
        
        # Replace this with your actual user list logic
        all_chat_ids = fetch_all_chat_ids()

        for chat_id in all_chat_ids:
            # Send the quiz to the user
            send_telegram_message(chat_id, f"Today's Quiz: {question}")
            # Save the last quiz_id for the user
            
            user_last_quiz.put_item(Item={"chat_id": chat_id, "quiz_id": str(quiz_id)})
            
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

def send_telegram_message(chat_id, text,include_get_answer_button=False):
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
        payload["reply_markup"] = {
            "inline_keyboard": [
                [
                    {"text": "Get Answer", "callback_data": "/getAnswer"}
                ]
            ]
        }

    response = requests.post(url, json=payload)

    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")
    else:
        print(f"Message sent to chat_id {chat_id}: {text}")

# Initialize APScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_quiz, 'cron', hour=12, minute=55)  # Schedule at 9:00 AM daily
scheduler.start()

if __name__ == '__main__':
    app.run(port=5002)
