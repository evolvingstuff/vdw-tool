#!/usr/bin/env python3
"""
Script to upload data/attachments/ folder to S3 bucket vitdwiki2/public/attachments2/
Preserves the subfolder structure and uploads all files.
"""

import os
import boto3
from pathlib import Path
from dotenv import load_dotenv
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, ClientError
import mimetypes

# Configuration
LOCAL_FOLDER = "data/attachments"
BUCKET_NAME = "vitdwiki2"
S3_PREFIX = "public/attachments"


def load_aws_credentials():
    """Load AWS credentials from .env file"""
    load_dotenv()

    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')

    if not aws_access_key or not aws_secret_key:
        raise ValueError(
            "AWS credentials not found in .env file. Please ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set.")

    return aws_access_key, aws_secret_key, aws_region


def create_s3_client(access_key, secret_key, region):
    """Create and return S3 client"""
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        return s3_client
    except Exception as e:
        raise Exception(f"Failed to create S3 client: {str(e)}")


def get_content_type(file_path):
    """Get the content type for a file based on its extension"""
    content_type, _ = mimetypes.guess_type(file_path)
    return content_type or 'binary/octet-stream'


def upload_file_to_s3(s3_client, local_file_path, bucket_name, s3_key):
    """Upload a single file to S3"""
    try:
        content_type = get_content_type(local_file_path)

        s3_client.upload_file(
            local_file_path,
            bucket_name,
            s3_key,
            ExtraArgs={'ContentType': content_type}
        )
        return True
    except ClientError as e:
        print(f"Error uploading {local_file_path}: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error uploading {local_file_path}: {str(e)}")
        return False


def upload_attachments_folder():
    """Main function to upload the attachments folder to S3"""

    print("Starting upload process...")
    print(f"Local folder: {LOCAL_FOLDER}")
    print(f"S3 bucket: {BUCKET_NAME}")
    print(f"S3 prefix: {S3_PREFIX}")
    print("-" * 50)

    try:
        # Load AWS credentials
        aws_access_key, aws_secret_key, aws_region = load_aws_credentials()
        print(f"✓ AWS credentials loaded (region: {aws_region})")

        # Create S3 client
        s3_client = create_s3_client(aws_access_key, aws_secret_key, aws_region)
        print("✓ S3 client created")

        # Check if local folder exists
        local_path = Path(LOCAL_FOLDER)
        if not local_path.exists():
            raise FileNotFoundError(f"Local folder '{LOCAL_FOLDER}' does not exist")

        if not local_path.is_dir():
            raise NotADirectoryError(f"'{LOCAL_FOLDER}' is not a directory")

        print(f"✓ Local folder '{LOCAL_FOLDER}' found")

        # Get all files to upload
        files_to_upload = []
        for root, dirs, files in os.walk(LOCAL_FOLDER):
            for file in files:
                if file == '.DS_Store':
                    continue
                local_file_path = os.path.join(root, file)

                # Calculate relative path from the attachments folder
                relative_path = os.path.relpath(local_file_path, LOCAL_FOLDER)

                # Create S3 key (convert Windows paths to Unix-style)
                s3_key = f"{S3_PREFIX}/{relative_path.replace(os.sep, '/')}"

                files_to_upload.append((local_file_path, s3_key))

        if not files_to_upload:
            print("⚠️  No files found to upload")
            return

        print(f"✓ Found {len(files_to_upload)} files to upload")
        print("-" * 50)

        # Upload files
        successful_uploads = 0
        failed_uploads = 0

        # files_to_upload = files_to_upload[:250]  # TODO

        for i, (local_file_path, s3_key) in enumerate(files_to_upload, 1):
            print(f"[{i}/{len(files_to_upload)}] Uploading: {local_file_path}")
            print(f"                    → s3://{BUCKET_NAME}/{s3_key}")

            if upload_file_to_s3(s3_client, local_file_path, BUCKET_NAME, s3_key):
                print("                    ✓ Success")
                successful_uploads += 1
            else:
                print("                    ✗ Failed")
                failed_uploads += 1

            print()

        # Summary
        print("-" * 50)
        print("Upload Summary:")
        print(f"✓ Successful uploads: {successful_uploads}")
        if failed_uploads > 0:
            print(f"✗ Failed uploads: {failed_uploads}")
        print(f"📁 Files uploaded to: s3://{BUCKET_NAME}/{S3_PREFIX}/")

    except ValueError as e:
        print(f"❌ Configuration error: {str(e)}")
    except (NoCredentialsError, PartialCredentialsError):
        print("❌ AWS credentials error: Please check your .env file")
    except FileNotFoundError as e:
        print(f"❌ File error: {str(e)}")
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    raise Exception('Are you sure you ever need to run this again after 2025.10.25 ?')
    upload_attachments_folder()
