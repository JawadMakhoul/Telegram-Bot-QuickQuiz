import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError

def connect_to_dynamodb():
    try:
        # Initialize DynamoDB resource
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')  # Replace with your region

        # Access a table (replace 'YourTableName' with your table name)
        table = dynamodb.Table('Quiz')

        # Example: Scan the table
        response = table.scan()
        items = response['Items']

        #print("Items in table:", items)

    except NoCredentialsError:
        print("No credentials found. Ensure the IAM role is attached to your EC2 instance.")
    except PartialCredentialsError:
        print("Partial credentials found. Check IAM role permissions.")
    except Exception as e:
        print("An error occurred:", str(e))

if __name__ == "__main__":
    connect_to_dynamodb