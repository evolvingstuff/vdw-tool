import os
import subprocess
import shutil
from tqdm import tqdm

def build_hugo_site():
    """Build Hugo site from posts/ markdown files using hugo_stuff/ configuration"""
    print("🏗️  Building Hugo site...")
    
    try:
        # Check if posts directory exists and has content
        if not os.path.exists('posts') or not os.listdir('posts'):
            print("❌ No posts/ directory found or it's empty. Run 'Sync Posts from S3' first.")
            return False
        
        # Check if hugo_stuff directory exists
        hugo_stuff_path = '_src/hugo_stuff'
        if not os.path.exists(hugo_stuff_path):
            print("❌ Hugo configuration not found at _src/hugo_stuff/")
            return False
        
        # Create temporary hugo site structure
        site_dir = 'hugo_site_build'
        if os.path.exists(site_dir):
            shutil.rmtree(site_dir)
        
        print("📁 Setting up Hugo site structure...")
        os.makedirs(site_dir)
        os.makedirs(f'{site_dir}/content/posts', exist_ok=True)
        os.makedirs(f'{site_dir}/layouts', exist_ok=True)
        os.makedirs(f'{site_dir}/static', exist_ok=True)
        
        # Copy hugo configuration
        shutil.copy(f'{hugo_stuff_path}/hugo.toml', f'{site_dir}/hugo.toml')
        
        # Copy layouts
        layout_files = ['baseof.html', 'index.html', 'list.html', 'single.html', 'taxonomy.html', 'terms.html']
        for layout_file in layout_files:
            if os.path.exists(f'{hugo_stuff_path}/{layout_file}'):
                shutil.copy(f'{hugo_stuff_path}/{layout_file}', f'{site_dir}/layouts/{layout_file}')
        
        # Copy shortcodes if they exist
        if os.path.exists(f'{hugo_stuff_path}/shortcodes'):
            shutil.copytree(f'{hugo_stuff_path}/shortcodes', f'{site_dir}/layouts/shortcodes')
        
        # Copy static files
        if os.path.exists(f'{hugo_stuff_path}/static'):
            shutil.copytree(f'{hugo_stuff_path}/static', f'{site_dir}/static', dirs_exist_ok=True)
        
        # Copy all markdown files from posts/ to content/posts/
        print("📄 Copying markdown files...")
        md_files = [f for f in os.listdir('posts') if f.endswith('.md')]
        
        with tqdm(total=len(md_files), desc="Copying files", unit="files") as pbar:
            for filename in md_files:
                shutil.copy(f'posts/{filename}', f'{site_dir}/content/posts/{filename}')
                pbar.update(1)
        
        print(f"📦 Copied {len(md_files)} markdown files")
        
        # Build the Hugo site
        print("🔨 Running Hugo build...")
        result = subprocess.run(['hugo'], cwd=site_dir, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Create output directory
            output_dir = 'hugo_output'
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            
            # Move built site to output directory
            shutil.move(f'{site_dir}/public', output_dir)
            
            # Clean up temporary build directory
            shutil.rmtree(site_dir)
            
            print(f"✅ Hugo site built successfully!")
            print(f"📁 Output available in: {output_dir}/")
            print(f"🌐 Open {output_dir}/index.html in a browser to view the site")
            return True
        else:
            print(f"❌ Hugo build failed:")
            print(f"Error: {result.stderr}")
            print(f"Output: {result.stdout}")
            return False
            
    except Exception as e:
        print(f"❌ Error building Hugo site: {e}")
        return False

if __name__ == '__main__':
    build_hugo_site()