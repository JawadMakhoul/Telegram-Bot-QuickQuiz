import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


def connect_to_dynamodb():
    try:
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Update region if needed
        table = dynamodb.Table('Quiz')  # Replace 'Quiz' with your actual table name
        return table
    except Exception as e:
        print(f"Error connecting to DynamoDB: {e}")
        return None

if __name__ == "__main__":
    connect_to_dynamodb