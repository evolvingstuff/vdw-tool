
import os
from config import s3_bucket_arn
from aws_config import get_s3_client

def sync_posts():
    """Sync posts/ folder from S3 bucket to local directory"""
    print("Syncing posts from S3...")
    
    # Get S3 client with credentials
    s3_client = get_s3_client()
    if not s3_client:
        print("Failed to connect to AWS. Please check your credentials.")
        return
    
    # Extract bucket name from ARN
    bucket_name = s3_bucket_arn.split(':')[-1]
    
    # Create posts directory if it doesn't exist
    posts_dir = 'posts'
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)
        print(f"Created {posts_dir}/ directory")
    
    try:
        # List objects in S3 bucket with posts/ prefix
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix='posts/')
        
        if 'Contents' not in response:
            print("No posts found in S3 bucket")
            return
        
        downloaded_count = 0
        for obj in response['Contents']:
            # Skip the posts/ folder itself
            if obj['Key'] == 'posts/':
                continue
                
            # Get the local file path
            local_path = obj['Key']  # This will be 'posts/filename.ext'
            
            # Create subdirectories if needed
            local_dir = os.path.dirname(local_path)
            if local_dir and not os.path.exists(local_dir):
                os.makedirs(local_dir)
            
            # Download the file
            print(f"Downloading {obj['Key']}...")
            s3_client.download_file(bucket_name, obj['Key'], local_path)
            downloaded_count += 1
        
        print(f"Successfully downloaded {downloaded_count} files to {posts_dir}/")
        
    except Exception as e:
        print(f"Error syncing posts: {e}")

def main():
    print('Master Script')
    print('')
    print('Options:')
    print('1) Hello World')
    print('2) Sync Posts from S3')
    print('3) Exit')

    while True:
        response = input('>> ')
        if response == '1':
            print('Hello World')
        elif response == '2':
            sync_posts()
        elif response == '3':
            print('Goodbye')
            break
        else:
            print('Invalid option')


if __name__ == '__main__':
    main()
