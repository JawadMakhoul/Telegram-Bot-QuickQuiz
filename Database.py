import boto3

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Quizzes')

# Add a quiz question
table.put_item(Item={
    'QuizID': '2',
    'Question': 'What is the capital of Italy?',
    'Answer': 'Rome',
    'Status': 'Pending'
})