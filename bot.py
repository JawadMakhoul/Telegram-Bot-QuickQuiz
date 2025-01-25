from flask import Flask, request, jsonify, Response
import requests
from dynamodb_connect import connect_to_dynamodb  # Your existing file to connect to DynamoDB

app = Flask(__name__)

TOKEN = '7467453386:AAEPsIImeqVnwNfeARnSU_WGeqMVtbTqRXM'
TELEGRAM_INIT_WEBHOOK_URL = 'https://api.telegram.org/bot{}/setWebhook?url=https://https://63fe-2a06-c701-7a9c-3e00-cc5-3b2-1c73-7e42.ngrok-free.app/message'.format(TOKEN)

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
            answer = get_last_quiz_answer()
            send_telegram_message(chat_id, answer)
        else:
            send_telegram_message(chat_id, "Got it!")

        return Response("success", status=200)
    else:
        return Response("GET method not allowed", status=405)


def get_last_quiz_answer():
    """
    Fetch the answer for the last quiz from DynamoDB.
    """
    try:
        # Calculate yesterday's ordinal date for the quiz_id
        yesterday = datetime.now().date() - timedelta(days=1)
        quiz_id = str(yesterday.toordinal())

        # Query DynamoDB for the quiz answer
        quiz_data = quiz_table.get_item(Key={"quiz_id": quiz_id}).get('Item', {})
        if quiz_data:
            return f"The answer to yesterday's quiz is: {quiz_data.get('answer', 'No answer available.')}"
        else:
            return "No quiz was available yesterday."
    except Exception as e:
        print(f"Error fetching last quiz answer: {str(e)}")
        return "There was an error fetching the answer. Please try again later."


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
