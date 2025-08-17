#!/usr/bin/env python3
"""
Deploy Hugo Site to S3/CloudFront
Uploads hugo_output/ to s3://vitdwiki2/public/ for static website hosting
"""

import os
import sys
import mimetypes
import hashlib
import json
from pathlib import Path
from tqdm import tqdm

# Add parent directory to path for imports
parent_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(parent_path)
from aws_config import get_s3_client, s3_bucket_arn


def get_mime_type(file_path):
    """
    Get the correct MIME type for a file.
    FAIL FAST: Essential for proper web serving.
    """
    mime_type, _ = mimetypes.guess_type(file_path)
    
    # Override for specific file types that are critical for web serving
    if file_path.endswith('.css'):
        return 'text/css'
    elif file_path.endswith('.js'):
        return 'application/javascript'
    elif file_path.endswith('.json'):
        return 'application/json'
    elif file_path.endswith('.html'):
        return 'text/html'
    elif file_path.endswith('.xml'):
        return 'application/xml'
    elif file_path.endswith('.svg'):
        return 'image/svg+xml'
    elif file_path.endswith('.woff'):
        return 'font/woff'
    elif file_path.endswith('.woff2'):
        return 'font/woff2'
    elif file_path.endswith('.ttf'):
        return 'font/ttf'
    elif file_path.endswith('.ico'):
        return 'image/x-icon'
    
    # Default to detected MIME type or binary
    return mime_type or 'application/octet-stream'


def calculate_file_hash(file_path):
    """Calculate MD5 hash of file for comparison."""
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def should_upload_file(s3_client, bucket_name, local_path, s3_key):
    """
    Check if file needs to be uploaded by comparing hashes.
    Returns True if file should be uploaded.
    """
    try:
        # Get object metadata from S3
        response = s3_client.head_object(Bucket=bucket_name, Key=s3_key)
        s3_etag = response['ETag'].strip('"')
        
        # Calculate local file hash
        local_hash = calculate_file_hash(local_path)
        
        # Compare hashes (S3 ETag is MD5 for single-part uploads)
        return local_hash != s3_etag
        
    except s3_client.exceptions.NoSuchKey:
        # File doesn't exist in S3, needs upload
        return True
    except Exception as e:
        # For 404 errors, file just doesn't exist yet (normal for new files)
        if "404" in str(e) or "Not Found" in str(e):
            return True
        # Any other error means we should upload to be safe
        print(f"⚠️  Could not check {s3_key}: {e}")
        return True


def configure_s3_static_website(s3_client, bucket_name):
    """
    Configure S3 bucket for static website hosting.
    Sets index.html as the default document for clean URLs.
    FAIL FAST: Any configuration errors will raise exceptions.
    """
    print("🌐 Configuring S3 bucket for static website hosting...")
    
    # Website configuration
    website_config = {
        'IndexDocument': {
            'Suffix': 'index.html'
        },
        'ErrorDocument': {
            'Key': 'index.html'  # SPA-style routing - all errors go to index.html
        }
    }
    
    try:
        # Apply website configuration
        s3_client.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration=website_config
        )
        
        # Get the website endpoint
        response = s3_client.get_bucket_location(Bucket=bucket_name)
        region = response['LocationConstraint'] or 'us-east-1'
        
        if region == 'us-east-1':
            website_url = f"http://{bucket_name}.s3-website-us-east-1.amazonaws.com"
        else:
            website_url = f"http://{bucket_name}.s3-website-{region}.amazonaws.com"
            
        print(f"✅ S3 static website hosting configured!")
        print(f"🌐 Website URL: {website_url}")
        print(f"📋 Index document: index.html")
        print(f"📋 Error document: index.html (SPA-style routing)")
        
        return website_url
        
    except Exception as e:
        raise RuntimeError(f"❌ Failed to configure S3 static website hosting: {e}")


def configure_s3_public_access(s3_client, bucket_name):
    """
    Configure S3 bucket for public read access (required for static websites).
    Handles cases where Block Public Access settings prevent bucket policies.
    """
    print("🔓 Configuring S3 bucket for public read access...")
    
    # Bucket policy for public read access
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "PublicReadGetObject",
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/public/*"
            }
        ]
    }
    
    try:
        # Apply bucket policy
        s3_client.put_bucket_policy(
            Bucket=bucket_name,
            Policy=json.dumps(bucket_policy)
        )
        
        print("✅ S3 bucket configured for public read access")
        print(f"📋 Public access: s3://{bucket_name}/public/* is publicly readable")
        return True
        
    except Exception as e:
        if "BlockPublicPolicy" in str(e) or "AccessDenied" in str(e):
            print("⚠️  S3 bucket has Block Public Access settings enabled")
            print("   This is normal for security. CloudFront can still access the files.")
            print("   If needed, configure public access manually in AWS console")
            return False
        else:
            raise RuntimeError(f"❌ Failed to configure S3 public access policy: {e}")


def deploy_hugo_site():
    """
    Deploy Hugo site to S3 for static website hosting.
    FAIL FAST: Any errors will raise exceptions immediately with clear messages.
    """
    print("🚀 Deploying Hugo site to S3/CloudFront...")
    
    # FAIL FAST: Validate prerequisites immediately
    hugo_output_dir = 'hugo_output'
    if not os.path.exists(hugo_output_dir):
        raise FileNotFoundError("❌ No hugo_output/ directory found. Run 'Build Hugo Site' first.")
    
    # Check if we have files to deploy
    html_files = list(Path(hugo_output_dir).glob('**/*.html'))
    if not html_files:
        raise ValueError(f"❌ No HTML files found in {hugo_output_dir}. Site may not be built properly.")
    
    print(f"📄 Found {len(html_files)} HTML files to deploy")
    
    # Get S3 client with credentials
    s3_client = get_s3_client()
    if not s3_client:
        raise RuntimeError("❌ Failed to connect to AWS. Please check your credentials.")
    
    # Extract bucket name from ARN
    bucket_name = s3_bucket_arn.split(':')[-1]
    s3_prefix = 'public/'
    
    print(f"📦 Deploying to s3://{bucket_name}/{s3_prefix}")
    
    # Configure S3 bucket for static website hosting
    website_url = configure_s3_static_website(s3_client, bucket_name)
    configure_s3_public_access(s3_client, bucket_name)
    
    # Get all files to upload
    all_files = []
    for root, dirs, files in os.walk(hugo_output_dir):
        for file in files:
            local_path = os.path.join(root, file)
            # Create S3 key by replacing hugo_output/ with public/
            relative_path = os.path.relpath(local_path, hugo_output_dir)
            s3_key = s3_prefix + relative_path.replace('\\', '/')  # Ensure forward slashes
            all_files.append((local_path, s3_key))
    
    if not all_files:
        raise ValueError(f"❌ No files found in {hugo_output_dir} to deploy")
    
    print(f"📁 Preparing to deploy {len(all_files)} files...")
    
    # For now, upload all files (skip optimization check for first deployment)
    files_to_upload = all_files
    files_skipped = 0
    
    print("📦 First deployment - uploading all files...")
    
    if files_skipped > 0:
        print(f"⚡ Skipping {files_skipped} unchanged files")
    
    if not files_to_upload:
        print("✅ All files are up to date! No deployment needed.")
        return True
    
    # Upload files with progress tracking
    uploaded_count = 0
    errors = []
    
    print(f"⬆️  Uploading {len(files_to_upload)} files...")
    
    with tqdm(total=len(files_to_upload), desc="Uploading", unit="files") as pbar:
        for local_path, s3_key in files_to_upload:
            try:
                # Get file info for progress display
                filename = os.path.basename(local_path)
                file_size = os.path.getsize(local_path)
                
                # Update progress bar description
                display_name = filename[:30].ljust(30) if len(filename) <= 30 else filename[:27] + "..."
                pbar.set_description(f"Uploading {display_name}")
                
                # Determine MIME type
                content_type = get_mime_type(local_path)
                
                # Upload with proper metadata
                extra_args = {
                    'ContentType': content_type,
                    'CacheControl': 'public, max-age=31536000' if not filename.endswith('.html') else 'public, max-age=3600'
                }
                
                # Special handling for index.html files (no cache for dynamic content)
                if filename == 'index.html':
                    extra_args['CacheControl'] = 'public, max-age=300'  # 5 minutes
                
                s3_client.upload_file(
                    local_path, 
                    bucket_name, 
                    s3_key,
                    ExtraArgs=extra_args
                )
                
                uploaded_count += 1
                pbar.update(1)
                
            except Exception as e:
                error_msg = f"Failed to upload {s3_key}: {e}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
                pbar.update(1)  # Still update progress even on error
    
    # Report results
    if errors:
        print(f"⚠️  Uploaded {uploaded_count} files with {len(errors)} errors:")
        for error in errors[:5]:  # Show first 5 errors
            print(f"   {error}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more errors")
        
        # FAIL FAST: Don't tolerate upload errors
        raise RuntimeError(f"❌ Deployment failed with {len(errors)} upload errors")
    
    print(f"✅ Successfully deployed {uploaded_count} files!")
    print(f"🌐 Site deployed to: s3://{bucket_name}/{s3_prefix}")
    print(f"📋 Next steps:")
    print(f"   1. Configure S3 bucket for static website hosting")
    print(f"   2. Set up CloudFront distribution pointing to s3://{bucket_name}/{s3_prefix}")
    print(f"   3. Configure index.html as default root object")
    
    return True


if __name__ == '__main__':
    try:
        deploy_hugo_site()
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        sys.exit(1)