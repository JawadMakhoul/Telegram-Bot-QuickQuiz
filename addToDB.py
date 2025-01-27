import boto3

# Initialize the DynamoDB resource
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace with your AWS region
table_name = 'Quiz'  # Replace with your table name
quiz_table = dynamodb.Table(table_name)

# List of quizzes
math_quizzes = [
        {"quiz_id": "31", "question": "What is the square root of 64?", "answer": "8"},
        {"quiz_id": "32", "question": "What is 15 × 3?", "answer": "45"},
        {"quiz_id": "33", "question": "If a triangle has angles of 60° and 60°, what is the third angle?", "answer": "60°"},
        {"quiz_id": "34", "question": "What is the value of π (pi) rounded to two decimal places?", "answer": "3.14"},
        {"quiz_id": "35", "question": "Solve: 12 ÷ (3 × 2)", "answer": "2"},
        {"quiz_id": "36", "question": "What is the perimeter of a square with side length 5?", "answer": "20"},
        {"quiz_id": "37", "question": "How many degrees are there in a right angle?", "answer": "90°"},
        {"quiz_id": "38", "question": "Solve: 7² + 4", "answer": "53"},
        {"quiz_id": "39", "question": "If a rectangle has a length of 10 and a width of 5, what is its area?", "answer": "50"},
        {"quiz_id": "40", "question": "What is the factorial of 4 (4!)?", "answer": "24"}
    ]

# Batch write function
def batch_write_quizzes():
    try:
        with quiz_table.batch_writer() as batch:
            for quiz in math_quizzes:
                batch.put_item(Item=quiz)
                print(f"Added quiz: {quiz['quiz_id']}")
        print("All quizzes added successfully.")
    except Exception as e:
        print(f"Error adding quizzes: {str(e)}")

# Call the function to add quizzes
batch_write_quizzes()