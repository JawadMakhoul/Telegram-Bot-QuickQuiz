import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


def connect_to_dynamodb_quizTable():
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Update region if needed
        table = dynamodb.Table('Quiz')  # Replace 'Quiz' with your actual table name
        return table
    except Exception as e:
        print(f"Error connecting to DynamoDB: {e}")
        return None
    
def connect_to_dynamodb_userLastQuizTable():
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Update region if needed
        table = dynamodb.Table('user_last_quiz')  # Replace 'Quiz' with your actual table name
        return table
    except Exception as e:
        print(f"Error connecting to DynamoDB: {e}")
        return None

if __name__ == "__main__":
    connect_to_dynamodb_quizTable
    connect_to_dynamodb_userLastQuizTable