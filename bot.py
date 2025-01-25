from flask import Flask, request, jsonify, Response
import requests
from dynamodb_connect import connect_to_dynamodb  # Your existing file to connect to DynamoDB

app = Flask(__name__)

TOKEN = '7467453386:AAEPsIImeqVnwNfeARnSU_WGeqMVtbTqRXM'
TELEGRAM_INIT_WEBHOOK_URL = 'https://api.telegram.org/bot{}/setWebhook?url=https://https://8252-2a06-c701-7a9c-3e00-cc5-3b2-1c73-7e42.ngrok-free.app/message'.format(TOKEN)
quiz_table = connect_to_dynamodb()

user_last_quiz = {}
requests.get(TELEGRAM_INIT_WEBHOOK_URL)

quiz_table = connect_to_dynamodb()  # Connect to the Quiz table


@app.route('/message', methods=['GET', 'POST'])
def handle_message():
    print(f"Request method: {request.method}")
    if request.method == 'POST':
        data = request.get_json()

        # Validate incoming data
        if not data or 'message' not in data:
            return Response("Invalid request", status=400)

        chat_id = data['message']['chat']['id']
        text = data['message'].get('text', '').strip().lower()

        # Handle /start command
        if text == '/start':
            send_telegram_message(chat_id, "Hello! Welcome to the bot. You'll receive a quiz daily!")
        # Handle /getAnswer command
        elif text == '/getanswer':
            answer = get_last_quiz_answer(chat_id)
            send_telegram_message(chat_id, answer)
        else:
            send_telegram_message(chat_id, "Got it!")

        return Response("success", status=200)
    else:
        return Response("GET method not allowed", status=405)

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
        #question = "TEEEEeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeEEST"
        # Replace this with your actual user list logic
        all_chat_ids = fetch_all_chat_ids()

        for chat_id in all_chat_ids:
            # Send the quiz to the user
            send_telegram_message(chat_id, f"Today's Quiz: {question}")

            # Save the last quiz_id for the user
            user_last_quiz[chat_id] = quiz_id
    except Exception as e:
        print(f"Error sending daily quiz: {str(e)}")

def get_last_quiz_answer(chat_id):
    """
    Fetch the answer for the last quiz sent to a specific user.
    """
    try:
        # Get the last quiz_id for the user
        quiz_id = user_last_quiz.get(chat_id)
        
        if not quiz_id:
            return "No quiz has been sent to you yet. Please wait for the next quiz."

        # Fetch the quiz from DynamoDB
        
        quiz_data = quiz_table.get_item(Key={"quiz_id": quiz_id}).get('question', {})
        
        if quiz_data:
            return f"The answer to your last quiz is: {quiz_data.get('answer', 'No answer available.')}"
        else:
            return "Unable to retrieve the quiz answer."
    except Exception as e:
        print(f"Error fetching last quiz answer: {str(e)}")
        return "There was an error fetching the answer. Please try again later."


def fetch_all_chat_ids():
    """
    Retrieve all chat IDs for broadcasting quizzes.
    """
    # Replace this logic with a proper method to retrieve all user chat IDs
    return ["6553509026", "812149678"]

def send_telegram_message(chat_id, text):
    """
    Send a message to the Telegram user.
    """
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    params = {"chat_id": chat_id, "text": text}
    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Failed to send message: {response.text}")
    else:
        print(f"Message sent to chat_id {chat_id}: {text}")

if __name__ == '__main__':
    app.run(port=5002)
