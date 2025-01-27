import boto3

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace with your AWS region
table_name = 'Quiz'  # Replace with your table name
quiz_table = dynamodb.Table(table_name)

# List of quizzes
more_quizzes = [
    {"quiz_id": "21", "question": "What is the hottest planet in the solar system?", "answer": "Venus"},
    {"quiz_id": "22", "question": "What is the smallest country in the world by area?", "answer": "Vatican City"},
    {"quiz_id": "23", "question": "How many bones are there in the human body?", "answer": "206"},
    {"quiz_id": "24", "question": "What is the largest mammal in the world?", "answer": "Blue Whale"},
    {"quiz_id": "25", "question": "What is the largest land animal?", "answer": "African Elephant"},
    {"quiz_id": "26", "question": "Which planet is known as the 'Red Planet'?", "answer": "Mars"},
    {"quiz_id": "27", "question": "Who invented the telephone?", "answer": "Alexander Graham Bell"},
    {"quiz_id": "28", "question": "What is the longest-running Broadway musical?", "answer": "The Phantom of the Opera"},
    {"quiz_id": "29", "question": "What is the capital of Australia?", "answer": "Canberra"},
    {"quiz_id": "30", "question": "In Greek mythology, who is the god of the sea?", "answer": "Poseidon"}
]

# Batch write function
def batch_write_quizzes():
    try:
        with quiz_table.batch_writer() as batch:
            for quiz in more_quizzes:
                batch.put_item(Item=quiz)
                print(f"Added quiz: {quiz['quiz_id']}")
        print("All quizzes added successfully.")
    except Exception as e:
        print(f"Error adding quizzes: {str(e)}")

# Call the function to add quizzes
batch_write_quizzes()