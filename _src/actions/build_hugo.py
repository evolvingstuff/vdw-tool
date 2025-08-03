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
from tag_processor import load_ontology_engine, process_markdown_file, write_processed_markdown, analyze_tag_expansion, print_expansion_analysis

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
    
    # Process markdown files with ontology-based tag expansion
    print("📄 Processing markdown files with ontology tag expansion...")
    md_files = [f for f in os.listdir('posts') if f.endswith('.md')]
    
    if not md_files:
        raise ValueError("❌ No markdown files found in posts/ directory")
    
    # Load ontology engine
    ontology_file = 'ontology.txt'
    if os.path.exists(ontology_file):
        print("🧠 Loading ontology engine for tag expansion...")
        try:
            ontology_engine = load_ontology_engine(ontology_file)
        except Exception as e:
            print(f"⚠️  Warning: Failed to load ontology engine: {e}")
            print("📄 Falling back to simple file copying without tag expansion")
            ontology_engine = None
    else:
        print(f"⚠️  Ontology file not found at {ontology_file}, skipping tag expansion")
        ontology_engine = None
    
    # Process files with tag expansion if ontology is available
    processed_files = []
    with tqdm(total=len(md_files), desc="Processing markdown files", unit="files") as pbar:
        for filename in md_files:
            source_path = os.path.join('posts', filename)
            target_path = os.path.join(content_posts_dir, filename)
            
            if ontology_engine:
                try:
                    # Process with ontology tag expansion
                    processed_data = process_markdown_file(source_path, ontology_engine)
                    write_processed_markdown(processed_data, target_path)
                    processed_files.append(processed_data)
                    pbar.set_postfix(tags_added=processed_data['tags_added'])
                except Exception as e:
                    print(f"❌ Failed to process {filename} with ontology: {e}")
                    # FAIL FAST: Don't fall back to copying, raise the error
                    raise RuntimeError(f"❌ Ontology processing failed for {filename}: {e}")
            else:
                # Simple copy without tag expansion
                shutil.copy2(source_path, target_path)
            
            pbar.update(1)
    
    if ontology_engine and processed_files:
        # Analyze and report tag expansion results
        analysis = analyze_tag_expansion(processed_files)
        print(f"📦 Processed {len(md_files)} markdown files with ontology tag expansion")
        print(f"📊 Tag expansion summary: {analysis['files_with_expansion']}/{analysis['total_files']} files expanded, "
              f"{analysis['expansion_factor']:.1f}x expansion factor")
        
        # FAIL FAST: If we have a large ontology but no tag expansion, something is wrong
        if analysis['total_files'] > 100 and analysis['files_with_expansion'] == 0:
            print(f"🐛 DEBUGGING ONTOLOGY FAILURE:")
            print(f"🐛 Text mappings loaded: {len(ontology_engine.text_mapping.text_to_tags)}")
            print(f"🐛 Regex patterns loaded: {len(ontology_engine.text_mapping.regex_patterns)}")
            print(f"🐛 Sample text mappings: {list(ontology_engine.text_mapping.text_to_tags.items())[:5]}")
            
            # Test with first processed file
            if processed_files:
                test_file = processed_files[0]
                print(f"🐛 Testing first file: {os.path.basename(test_file['file_path'])}")
                print(f"🐛 Original tags: {test_file['original_tags']}")
                print(f"🐛 Expanded tags: {test_file['expanded_tags']}")
                print(f"🐛 Associated tags: {test_file['associated_tags']}")
                
                # Test text extraction directly on content snippet
                content_snippet = test_file.get('content', '')[:500]  # First 500 chars
                if 'vitamin' in content_snippet.lower():
                    text_derived = ontology_engine.text_mapping.extract_tags_from_text(content_snippet)
                    print(f"🐛 Text-derived from snippet: {text_derived}")
                    
            raise RuntimeError(f"❌ ONTOLOGY FAILURE: Processed {analysis['total_files']} files but 0 got tag expansion. "
                             f"This indicates the ontology engine is not working properly. "
                             f"Expected expansion with vitamin D research content and comprehensive ontology rules.")
        
        # Print detailed analysis if significant expansion occurred
        if analysis['expansion_factor'] > 1.1:  # More than 10% expansion
            print_expansion_analysis(analysis)
    else:
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