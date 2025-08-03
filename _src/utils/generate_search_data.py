import os
import json
import frontmatter
from collections import defaultdict, Counter
from pathlib import Path
import re
from nltk.corpus import stopwords
import nltk

# Download stopwords if not already present
try:
    stopwords.words('english')
except:
    nltk.download('stopwords')

def generate_search_data():
    """
    Generate search data files (cooccurrences.json, text_suggestions.json) from hugo_output/ content.
    FAIL FAST: Any errors will raise exceptions immediately with clear messages.
    """
    print("📊 Generating search data files...")
    
    # FAIL FAST: Validate prerequisites immediately
    hugo_output_dir = 'hugo_output'
    if not os.path.exists(hugo_output_dir):
        raise FileNotFoundError("❌ No hugo_output/ directory found. Run 'Build Hugo Site' first.")
    
    posts_dir = 'posts'
    if not os.path.exists(posts_dir):
        raise FileNotFoundError("❌ No posts/ directory found. Run 'Sync Posts from S3' first.")
    
    # Create search data directories in hugo_output
    js_dir = os.path.join(hugo_output_dir, 'js')
    search_dir = os.path.join(hugo_output_dir, 'search')
    os.makedirs(js_dir, exist_ok=True)
    os.makedirs(search_dir, exist_ok=True)
    
    print("🔍 Analyzing markdown files for search data...")
    
    # Process all markdown files to extract tags and generate search data
    cooccurrences = defaultdict(set)
    all_terms = Counter()
    page_tags = {}
    
    # Get all markdown files
    md_files = list(Path(posts_dir).glob('*.md'))
    if not md_files:
        raise ValueError("❌ No markdown files found in posts/ directory")
    
    print(f"📄 Processing {len(md_files)} markdown files...")
    
    # Extract stopwords for filtering
    try:
        stop_words = set(stopwords.words('english'))
    except:
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
    
    processed_files = 0
    for md_file in md_files:
        # FAIL FAST: Any frontmatter processing error should stop the build  
        post = frontmatter.load(md_file)
        
        # Extract tags from frontmatter
        tags = post.metadata.get('tags', [])
        if isinstance(tags, str):
            tags = [tags]
        
        # Normalize tags: convert to display format (spaces instead of underscores)
        normalized_tags = []
        for tag in tags:
            if isinstance(tag, str):
                # Convert from internal format (#tag_with_underscores) to display format
                display_tag = tag.replace('#', '').replace('_', ' ').strip()
                if display_tag:
                    normalized_tags.append(display_tag)
        
        # Store page tags
        page_id = md_file.stem  # filename without extension
        page_tags[page_id] = normalized_tags
        
        # Build cooccurrences: for each tag, track which other tags appear with it
        for i, tag1 in enumerate(normalized_tags):
            internal_tag1 = '#' + tag1.replace(' ', '_')  # Convert to internal format for storage
            for j, tag2 in enumerate(normalized_tags):
                if i != j:  # Don't include self-references
                    internal_tag2 = '#' + tag2.replace(' ', '_')
                    cooccurrences[internal_tag1].add(internal_tag2)
        
        # Extract terms from content for text suggestions
        content = post.content.lower()
        # Remove HTML tags and special characters, split into words
        clean_content = re.sub(r'<[^>]+>', ' ', content)
        clean_content = re.sub(r'[^a-zA-Z\s]', ' ', clean_content)
        words = clean_content.split()
        
        # Filter out stopwords and short words, count frequencies
        for word in words:
            word = word.strip()
            if len(word) > 2 and word not in stop_words:
                all_terms[word] += 1
        
        # Also count tag terms
        for tag in normalized_tags:
            all_terms[tag] += 10  # Give tags higher weight
        
        processed_files += 1
    
    if processed_files == 0:
        raise ValueError("❌ No markdown files were successfully processed")
    
    print(f"✅ Processed {processed_files} markdown files")
    
    # Convert cooccurrences sets to lists for JSON serialization
    cooccurrences_json = {}
    for tag, related_tags in cooccurrences.items():
        cooccurrences_json[tag] = list(related_tags)
    
    # Generate text suggestions (top terms by frequency)
    text_suggestions = {
        "text_suggestions": [
            {"term": term, "frequency": freq}
            for term, freq in all_terms.most_common(500)  # Top 500 terms
        ]
    }
    
    # Write cooccurrences.json to js/ directory (where search-suggestions.js expects it)
    cooccurrences_file = os.path.join(js_dir, 'cooccurrences.json')
    try:
        with open(cooccurrences_file, 'w', encoding='utf-8') as f:
            json.dump(cooccurrences_json, f, indent=2, ensure_ascii=False)
        print(f"📄 Generated cooccurrences.json with {len(cooccurrences_json)} tag relationships")
    except Exception as e:
        raise RuntimeError(f"❌ Failed to write cooccurrences.json: {e}")
    
    # Write text_suggestions.json to search/ directory (where existing files are)  
    suggestions_file = os.path.join(search_dir, 'text_suggestions.json')
    try:
        with open(suggestions_file, 'w', encoding='utf-8') as f:
            json.dump(text_suggestions, f, indent=2, ensure_ascii=False)
        print(f"📄 Generated text_suggestions.json with {len(text_suggestions['text_suggestions'])} terms")
    except Exception as e:
        raise RuntimeError(f"❌ Failed to write text_suggestions.json: {e}")
    
    # Generate page_id_to_tags.json for additional search functionality
    page_id_file = os.path.join(search_dir, 'page_id_to_tags.json')
    try:
        with open(page_id_file, 'w', encoding='utf-8') as f:
            json.dump(page_tags, f, indent=2, ensure_ascii=False)
        print(f"📄 Generated page_id_to_tags.json with {len(page_tags)} pages")
    except Exception as e:
        raise RuntimeError(f"❌ Failed to write page_id_to_tags.json: {e}")
    
    print("✅ Search data generation completed successfully!")
    print(f"📁 Search data files available in: {js_dir}/ and {search_dir}/")
    print(f"🏷️  Found {len(cooccurrences_json)} unique tags with relationships")
    print(f"🔤 Generated {len(text_suggestions['text_suggestions'])} text suggestions")
    
    return True

if __name__ == '__main__':
    generate_search_data()