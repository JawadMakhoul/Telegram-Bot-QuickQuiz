from flask import Flask, request, jsonify, Response
import requests
from dynamodb_connect import connect_to_dynamodb  # Your existing file to connect to DynamoDB
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

TOKEN = '7467453386:AAEPsIImeqVnwNfeARnSU_WGeqMVtbTqRXM'
TELEGRAM_INIT_WEBHOOK_URL = 'https://api.telegram.org/bot{}/setWebhook?url=https://8252-2a06-c701-7a9c-3e00-cc5-3b2-1c73-7e42.ngrok-free.app/message'.format(TOKEN)
user_quiz_table = connect_to_dynamodb()
quiz_table = connect_to_dynamodb()


user_last_quiz = {}
requests.get(TELEGRAM_INIT_WEBHOOK_URL)


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
            print("testttttttttttttttttttttttttttt")
            print(chat_id)
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
        print(quiz_data)
        if not quiz_data:
            print("No quiz available to send.")
            return

        quiz_id = quiz_data['quiz_id']
        question = quiz_data['question']

        # Replace this with your actual user list logic
        all_chat_ids = fetch_all_chat_ids()

        for chat_id in all_chat_ids:
            print("fffffffffffffffff")
            # Send the quiz to the user
            send_telegram_message(chat_id, f"Today's Quiz: {question}")
            # Save the last quiz_id for the user
            print("pppppppppppppp")
            user_quiz_table.put_item(Item={"chat_id": chat_id, "quiz_id": quiz_id})
            print("jjjjjjjjjjjjjjjj")
            print(user_last_quiz[chat_id])
            print(f"Updated DynamoDB for chat_id {chat_id} with quiz_id {quiz_id}")
           
    except Exception as e:
        print(f"Error sending daily quiz: {str(e)}")

def get_last_quiz_answer(chat_id):
    """
    Fetch the answer for the last quiz sent to a specific user.
    """
    try:
        print("rrrrrrrrrrrrr")
        response = user_quiz_table.get_item(Key={"chat_id": chat_id})
        print("tttttttttttt")
        user_data = response.get('Item', {})
        print("zzzzzzzzzzzz")
        # Get the last quiz_id for the user
        #print(f"user_last_quiz: {user_last_quiz}")
        #print(f"Looking up quiz_id for chat_id: {chat_id}")
        #print(user_last_quiz.get(chat_id))
        #quiz_id = str(user_last_quiz.get(chat_id)) # quiz_id is None it should be 1, chat_id is correct $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$
        
        if not user_data:
            return "No quiz has been sent to you yet. Please wait for the next quiz."
        
        print("xxxxxxxxxxxxxxxx")
        # Fetch the quiz from DynamoDB
        quiz_id = user_data.get('quiz_id')
        print(quiz_id)
        quiz_data = quiz_table.get_item(Key={"quiz_id": quiz_id}).get('Item', {})
        print(quiz_data)
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
    return ["812149678"]

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

# Initialize APScheduler
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_quiz, 'cron', hour=13, minute=29)  # Schedule at 9:00 AM daily
scheduler.start()

if __name__ == '__main__':
    app.run(port=5002)
