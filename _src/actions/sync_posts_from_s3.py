import os
import sys
# Add parent directory to path for imports
parent_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(parent_path)
from aws_config import s3_bucket_arn, get_s3_client
from tqdm import tqdm

def sync_posts():
    """Sync posts/ folder from S3 bucket to local directory"""
    print("Syncing posts from S3...")
    
    # Get S3 client with credentials
    s3_client = get_s3_client()
    if not s3_client:
        print("Failed to connect to AWS. Please check your credentials.")
        return False
    
    # Extract bucket name from ARN
    bucket_name = s3_bucket_arn.split(':')[-1]
    
    # Create posts directory if it doesn't exist
    posts_dir = 'posts'
    if not os.path.exists(posts_dir):
        os.makedirs(posts_dir)
        print(f"Created {posts_dir}/ directory")
    
    try:
        # List ALL objects in S3 bucket with posts/ prefix (handle pagination)
        print("📁 Listing files in S3 bucket...")
        all_objects = []
        continuation_token = None
        
        while True:
            # Prepare parameters for list_objects_v2
            params = {'Bucket': bucket_name, 'Prefix': 'posts/'}
            if continuation_token:
                params['ContinuationToken'] = continuation_token
            
            response = s3_client.list_objects_v2(**params)
            
            # Add objects from this page
            if 'Contents' in response:
                all_objects.extend(response['Contents'])
            
            # Check if there are more pages
            if response.get('IsTruncated', False):
                continuation_token = response.get('NextContinuationToken')
                print(f"📄 Found {len(all_objects)} files so far, getting more...")
            else:
                break
        
        if not all_objects:
            print("No posts found in S3 bucket")
            return False
        
        # Filter out the posts/ folder itself and prepare file list
        files_to_download = [obj for obj in all_objects if obj['Key'] != 'posts/']
        
        if not files_to_download:
            print("No files found in posts/ folder")
            return False
        
        # Calculate total size for progress tracking
        total_size = sum(obj['Size'] for obj in files_to_download)
        
        print(f"📦 Found {len(files_to_download)} files ({total_size / 1024 / 1024:.1f} MB total)")
        
        downloaded_count = 0
        
        # Create progress bar for overall download progress
        with tqdm(total=total_size, unit='B', unit_scale=True, desc="Downloading") as pbar:
            for obj in files_to_download:
                # Get the local file path
                local_path = obj['Key']  # This will be 'posts/filename.ext'
                
                # Create subdirectories if needed
                local_dir = os.path.dirname(local_path)
                if local_dir and not os.path.exists(local_dir):
                    os.makedirs(local_dir)
                
                # Update progress bar description with current file (fixed width)
                filename = os.path.basename(obj['Key'])
                # Truncate or pad filename to 30 characters for stable progress bar
                display_name = filename[:30].ljust(30) if len(filename) <= 30 else filename[:27] + "..."
                pbar.set_description(f"Downloading {display_name}")
                
                # Download the file
                s3_client.download_file(bucket_name, obj['Key'], local_path)
                downloaded_count += 1
                
                # Update progress bar
                pbar.update(obj['Size'])
        
        print(f"✅ Successfully downloaded {downloaded_count} files to {posts_dir}/")
        return True
        
    except Exception as e:
        print(f"❌ Error syncing posts: {e}")
        return False

if __name__ == '__main__':
    sync_posts()