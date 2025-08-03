import os
import subprocess
import shutil
import re
from tqdm import tqdm
from pathlib import Path
import sys
sys.path.append('_src/utils')
from build_search_index import build_search_index
from generate_search_data import generate_search_data

def clean_directory(directory, preserve_hidden=True):
    """
    Clean a directory by removing all its contents.
    If preserve_hidden is True, files and directories starting with '.' are preserved.
    FAIL FAST: Any errors during cleanup will raise exceptions immediately.
    """
    if not os.path.exists(directory):
        return
        
    for item in os.listdir(directory):
        # Skip hidden files/directories if preserve_hidden is True
        if preserve_hidden and item.startswith('.'):
            print(f"Preserving hidden item: {item}")
            continue
            
        path = os.path.join(directory, item)
        if os.path.isfile(path) or os.path.islink(path):
            os.unlink(path)
        elif os.path.isdir(path):
            shutil.rmtree(path)

def copy_hugo_layouts(hugo_stuff_path, site_dir):
    """
    Copy Hugo layouts with proper directory structure.
    Based on vitD hugo.py:92-127
    FAIL FAST: Missing files or copy errors will raise exceptions immediately.
    """
    layouts_dir = os.path.join(site_dir, 'layouts')
    default_dir = os.path.join(layouts_dir, '_default')
    
    os.makedirs(default_dir, exist_ok=True)
    
    # Copy layout files to _default directory
    layout_files = ['baseof.html', 'index.html', 'list.html', 'single.html', 'taxonomy.html', 'terms.html']
    for layout_file in layout_files:
        source_file = os.path.join(hugo_stuff_path, layout_file)
        if os.path.exists(source_file):
            target_file = os.path.join(default_dir, layout_file)
            shutil.copy2(source_file, target_file)
            print(f"📄 Copied layout: {layout_file}")
    
    # Copy shortcodes directory if it exists
    shortcodes_source = os.path.join(hugo_stuff_path, 'shortcodes')
    shortcodes_target = os.path.join(layouts_dir, 'shortcodes')
    if os.path.exists(shortcodes_source):
        if os.path.exists(shortcodes_target):
            shutil.rmtree(shortcodes_target)
        shutil.copytree(shortcodes_source, shortcodes_target)
        print(f"📁 Copied shortcodes to {shortcodes_target}")

def copy_hugo_config(hugo_stuff_path, site_dir):
    """
    Copy and potentially modify Hugo configuration.
    Based on vitD hugo.py:68-83
    FAIL FAST: Missing config or write errors will raise exceptions immediately.
    """
    source_config = os.path.join(hugo_stuff_path, 'hugo.toml')
    target_config = os.path.join(site_dir, 'hugo.toml')
    
    if not os.path.exists(source_config):
        raise FileNotFoundError(f"Hugo config not found at {source_config}")
    
    # Read the original config
    with open(source_config, 'r') as f:
        config_content = f.read()
    
    # Ensure baseURL is set to / for consistent URLs
    if 'baseURL = "' in config_content:
        config_content = re.sub(r'baseURL = ".*?"', 'baseURL = "/"', config_content)
        print("🔧 Set baseURL to '/' for local development")
    
    # Write the modified config
    with open(target_config, 'w') as f:
        f.write(config_content)
    
    print("📋 Copied Hugo configuration")

def copy_static_files(hugo_stuff_path, site_dir):
    """
    Copy static files (CSS, JS, etc) to Hugo static directory.
    Based on vitD hugo.py:186-193
    FAIL FAST: Copy errors will raise exceptions immediately.
    """
    source_static = os.path.join(hugo_stuff_path, 'static')
    dest_static = os.path.join(site_dir, 'static')
    
    if os.path.exists(source_static):
        # Remove existing static directory to avoid conflicts
        if os.path.exists(dest_static):
            shutil.rmtree(dest_static)
        
        # Copy entire static directory
        shutil.copytree(source_static, dest_static)
        print("📁 Copied static files (CSS, JS, etc)")

def build_hugo_site():
    """
    Build Hugo site from posts/ markdown files using hugo_stuff/ configuration.
    FAIL FAST: Any errors will raise exceptions immediately with clear messages.
    """
    print("🏗️  Building Hugo site...")
    
    # FAIL FAST: Validate prerequisites immediately
    if not os.path.exists('posts') or not os.listdir('posts'):
        raise FileNotFoundError("❌ No posts/ directory found or it's empty. Run 'Sync Posts from S3' first.")
    
    hugo_stuff_path = '_src/hugo_stuff'
    if not os.path.exists(hugo_stuff_path):
        raise FileNotFoundError(f"❌ Hugo configuration not found at {hugo_stuff_path}")
    
    # Clean up any existing build directory
    site_dir = 'hugo_site_build'
    if os.path.exists(site_dir):
        print(f"🧹 Cleaning existing build directory: {site_dir}")
        clean_directory(site_dir, preserve_hidden=True)
    else:
        os.makedirs(site_dir)
    
    # Set up Hugo site structure
    print("📁 Setting up Hugo site structure...")
    content_posts_dir = os.path.join(site_dir, 'content', 'posts')
    os.makedirs(content_posts_dir, exist_ok=True)
    
    # Copy Hugo configuration with local development settings
    copy_hugo_config(hugo_stuff_path, site_dir)
    
    # Copy layouts with proper _default directory structure  
    copy_hugo_layouts(hugo_stuff_path, site_dir)
    
    # Copy static files (CSS, JS, search data, etc)
    copy_static_files(hugo_stuff_path, site_dir)
    
    # Copy all markdown files from posts/ to content/posts/
    print("📄 Copying markdown files...")
    md_files = [f for f in os.listdir('posts') if f.endswith('.md')]
    
    if not md_files:
        raise ValueError("❌ No markdown files found in posts/ directory")
    
    with tqdm(total=len(md_files), desc="Copying markdown files", unit="files") as pbar:
        for filename in md_files:
            source_path = os.path.join('posts', filename)
            target_path = os.path.join(content_posts_dir, filename)
            shutil.copy2(source_path, target_path)
            pbar.update(1)
    
    print(f"📦 Copied {len(md_files)} markdown files")
    
    # Build the Hugo site
    print("🔨 Running Hugo build...")
    result = subprocess.run(['hugo'], cwd=site_dir, capture_output=True, text=True)
    
    # FAIL FAST: Hugo build must succeed completely
    if result.returncode != 0:
        error_msg = f"❌ Hugo build failed with return code {result.returncode}\n"
        error_msg += f"STDERR: {result.stderr}\n" 
        error_msg += f"STDOUT: {result.stdout}"
        raise RuntimeError(error_msg)
    
    # Verify that Hugo created the public directory
    public_dir = os.path.join(site_dir, 'public')
    if not os.path.exists(public_dir):
        raise RuntimeError("❌ Hugo build completed but no 'public' directory was created")
    
    # Create/clean output directory and move built site
    output_dir = 'hugo_output'
    if os.path.exists(output_dir):
        print(f"🧹 Cleaning existing output directory: {output_dir}")
        clean_directory(output_dir, preserve_hidden=True)
    else:
        os.makedirs(output_dir)
    
    # Move built site contents to output directory
    for item in os.listdir(public_dir):
        source_item = os.path.join(public_dir, item)
        target_item = os.path.join(output_dir, item)
        if os.path.isdir(source_item):
            shutil.copytree(source_item, target_item)
        else:
            shutil.copy2(source_item, target_item)
    
    # Clean up temporary build directory
    print(f"🧹 Cleaning up temporary build directory: {site_dir}")
    shutil.rmtree(site_dir)
    
    # Verify final output
    index_file = os.path.join(output_dir, 'index.html')
    if not os.path.exists(index_file):
        raise RuntimeError(f"❌ Build completed but no index.html found in {output_dir}")
    
    print(f"✅ Hugo site built successfully!")
    print(f"📁 Output available in: {output_dir}/")
    
    # Generate search data (cooccurrences.json, text_suggestions.json)
    # FAIL FAST: Search data generation failure should stop the build
    generate_search_data()
    
    # Build search index with Pagefind  
    # FAIL FAST: Search index creation failure should stop the build
    build_search_index()
    
    print(f"🌐 Hugo site with search ready! Open {output_dir}/index.html in a browser")
    return True

if __name__ == '__main__':
    build_hugo_site()