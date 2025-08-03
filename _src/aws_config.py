import os
from dotenv import load_dotenv, set_key
import boto3
from botocore.exceptions import ClientError
# AWS configuration
s3_bucket_arn = 'arn:aws:s3:::vitdwiki2'
region = 'us-west-2'

def load_aws_credentials():
    """Load AWS credentials from .env file"""
    load_dotenv()
    return {
        'access_key': os.getenv('AWS_ACCESS_KEY_ID'),
        'secret_key': os.getenv('AWS_SECRET_ACCESS_KEY'),
        'region': os.getenv('AWS_DEFAULT_REGION', region)
    }

def save_aws_credentials(access_key, secret_key, aws_region=region):
    """Save AWS credentials to .env file"""
    env_file = '.env'
    set_key(env_file, 'AWS_ACCESS_KEY_ID', access_key)
    set_key(env_file, 'AWS_SECRET_ACCESS_KEY', secret_key)
    set_key(env_file, 'AWS_DEFAULT_REGION', aws_region)

def prompt_for_credentials():
    """Prompt user for AWS credentials and save them"""
    print("\n" + "="*60)
    print("AWS CREDENTIALS NEEDED")
    print("="*60)
    print("\nTo get your AWS credentials:")
    print("1. Go to: https://console.aws.amazon.com")
    print("2. Log in with your regular username and password")
    print("3. Click your name (top right) → Security credentials")
    print("4. Scroll down to 'Access keys'")
    print("5. Click 'Create access key'")
    print("6. Choose 'Command Line Interface (CLI)'")
    print("7. Click 'Next' then 'Create access key'")
    print("8. Copy both values below (IMPORTANT: Save them now!)")
    print("\nNOTE: These are different from your regular login credentials.")
    print("="*60)
    
    access_key = input("\nAWS Access Key ID: ").strip()
    secret_key = input("AWS Secret Access Key: ").strip()
    
    save_aws_credentials(access_key, secret_key)
    print(f"Credentials saved to .env file (using region: {region}).")
    return access_key, secret_key, region

def get_s3_client():
    """Get authenticated S3 client"""
    creds = load_aws_credentials()
    
    if not creds['access_key'] or not creds['secret_key']:
        access_key, secret_key, aws_region = prompt_for_credentials()
        creds = {'access_key': access_key, 'secret_key': secret_key, 'region': aws_region}
    
    try:
        client = boto3.client(
            's3',
            aws_access_key_id=creds['access_key'],
            aws_secret_access_key=creds['secret_key'],
            region_name=creds['region']
        )
        # Test credentials
        client.list_buckets()
        return client
    except ClientError as e:
        print(f"AWS credentials error: {e}")
        print("Please check your credentials and try again.")
        # Remove invalid credentials
        if os.path.exists('.env'):
            os.remove('.env')
        return None