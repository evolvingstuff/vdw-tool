import os
import subprocess
import json
from pathlib import Path

def build_search_index():
    """
    Build Pagefind search index from hugo_output/ directory.
    FAIL FAST: Any errors will raise exceptions immediately with clear messages.
    """
    print("🔍 Building search index with Pagefind...")
    
    # FAIL FAST: Validate prerequisites immediately
    hugo_output_dir = 'hugo_output'
    if not os.path.exists(hugo_output_dir):
        raise FileNotFoundError("❌ No hugo_output/ directory found. Run 'Build Hugo Site' first.")
    
    # Check if we have HTML files to index
    posts_pattern = os.path.join(hugo_output_dir, 'posts')
    if not os.path.exists(posts_pattern):
        raise FileNotFoundError(f"❌ No posts/ directory found in {hugo_output_dir}")
    
    # Count HTML files to verify we have content to index
    html_files = list(Path(posts_pattern).glob('**/*.html'))
    if not html_files:
        raise ValueError(f"❌ No HTML files found in {posts_pattern} to index")
    
    print(f"📄 Found {len(html_files)} HTML files to index")
    
    # Run Pagefind indexing against our flat hugo_output structure
    print("🔨 Running Pagefind indexing...")
    
    # Clean up any existing pagefind directories first
    pagefind_dir = os.path.join(hugo_output_dir, 'pagefind')  # Actual location (no underscore)
    pagefind_dir_underscore = os.path.join(hugo_output_dir, '_pagefind')  # Expected location
    
    if os.path.exists(pagefind_dir):
        print("🧹 Cleaning existing pagefind directory...")
        import shutil
        shutil.rmtree(pagefind_dir)
    if os.path.exists(pagefind_dir_underscore):
        print("🧹 Cleaning existing _pagefind directory...")
        import shutil
        shutil.rmtree(pagefind_dir_underscore)
    
    try:
        # Run Pagefind with simpler glob pattern
        result = subprocess.run([
            'pagefind', 
            '--site', hugo_output_dir
        ], capture_output=True, text=True, check=False)
        
        # Print Pagefind output for debugging
        if result.stdout:
            print(f"📊 Pagefind output: {result.stdout.strip()}")
        if result.stderr:
            print(f"⚠️  Pagefind stderr: {result.stderr.strip()}")
        
        # FAIL FAST: Pagefind must succeed completely
        if result.returncode != 0:
            error_msg = f"❌ Pagefind indexing failed with return code {result.returncode}\n"
            error_msg += f"STDERR: {result.stderr}\n"
            error_msg += f"STDOUT: {result.stdout}"
            raise RuntimeError(error_msg)
        
        # Verify that Pagefind created files (check actual location)
        if not os.path.exists(pagefind_dir):
            raise RuntimeError("❌ Pagefind completed but no 'pagefind' directory was created")
        
        # Check for key Pagefind files
        required_files = ['pagefind.js', 'pagefind-ui.js', 'pagefind-ui.css']
        missing_files = []
        for file_name in required_files:
            if not os.path.exists(os.path.join(pagefind_dir, file_name)):
                missing_files.append(file_name)
        
        if missing_files:
            raise RuntimeError(f"❌ Pagefind missing required files: {', '.join(missing_files)}")
        
        print("✅ Pagefind search index built successfully!")
        print(f"📁 Search index available in: {pagefind_dir}/")
        print(f"🔍 Indexed {len(html_files)} HTML files")
        
        # Show some stats if available
        if result.stdout:
            print("📊 Pagefind output:", result.stdout.strip())
        
        return True
        
    except FileNotFoundError:
        raise RuntimeError("❌ Pagefind command not found. Ensure Pagefind is installed and in PATH.")
    except Exception as e:
        raise RuntimeError(f"❌ Unexpected error during Pagefind indexing: {e}")

if __name__ == '__main__':
    build_search_index()