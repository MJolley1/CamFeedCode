import boto3

# Creating the low level functional client
client = boto3.client(
    's3',
    aws_access_key_id='############',
    aws_secret_access_key='############',
    region_name='eu-west-2'
)

# Creating the high level object oriented interface
resource = boto3.resource(
    's3',
    aws_access_key_id='############',
    aws_secret_access_key='############',
    region_name='eu-west-2'
)

# creating the session output
session = boto3.Session(
    aws_access_key_id='############',
    aws_secret_access_key='############',
    region_name='eu-west-2'
)
