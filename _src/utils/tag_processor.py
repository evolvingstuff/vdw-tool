#!/usr/bin/env python3
"""
Tag Processing Utilities for VDW Tool
Handles markdown frontmatter processing and tag expansion using ontology engine
Ported from vitD project with FAIL FAST philosophy
"""

import os
import frontmatter
from typing import Dict, List, Set, Any, Optional

# Handle both relative and absolute imports
try:
    from .ontology_engine import OntologyEngine, augment_page_tags
    from .ontology_utils import parse_ontology_file, ontology_rules_to_engine_format
except ImportError:
    # Fallback for when running as script or from different context
    from ontology_engine import OntologyEngine, augment_page_tags
    from ontology_utils import parse_ontology_file, ontology_rules_to_engine_format


def load_ontology_engine(ontology_file_path: str) -> OntologyEngine:
    """
    Load and initialize ontology engine from ontology.txt file
    FAIL FAST: Any loading errors will raise exceptions immediately
    """
    if not os.path.exists(ontology_file_path):
        raise FileNotFoundError(f"❌ Ontology file not found: {ontology_file_path}")
    
    print(f"Loading ontology from {ontology_file_path}...")
    
    try:
        # Parse ontology rules
        parsed_rules = parse_ontology_file(ontology_file_path)
        engine_rules = ontology_rules_to_engine_format(parsed_rules)
        
        # Create and populate engine
        engine = OntologyEngine()
        engine.process_rules_from_parser(engine_rules)
        
        print(f"✅ Ontology engine loaded with {len(engine_rules)} rules")
        return engine
        
    except Exception as e:
        raise RuntimeError(f"❌ Failed to load ontology engine: {e}")


def process_markdown_file(file_path: str, ontology_engine: OntologyEngine) -> Dict[str, Any]:
    """
    Process a markdown file and expand its tags using the ontology engine
    FAIL FAST: Any processing errors will raise exceptions immediately
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"❌ Markdown file not found: {file_path}")
    
    try:
        # Load and parse frontmatter
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # Extract content and metadata
        content = post.content
        metadata = post.metadata.copy()
        
        # Get categories (if any) to use as initial tags - exactly like vitD: hugo.py:312-321
        categories = metadata.get('categories', [])
        
        # Convert categories to ontology format (replace spaces with underscores and add # prefix)
        # Example: "Cost savings with Vitamin D" -> "#Cost_savings_with_Vitamin_D"
        raw_tags = []
        for category in categories:
            # Replace spaces with underscores and add # prefix
            ontology_tag = f"#{category.replace(' ', '_')}"
            raw_tags.append(ontology_tag)
        
        # Create page structure for ontology processing
        page = {
            'text': content,
            'raw_tags': raw_tags
        }
        
        # Expand tags using ontology
        augmented_page = augment_page_tags(ontology_engine, page)
        
        # Get expanded tags and convert them back to human-readable format - exactly like vitD: hugo.py:337-346
        expanded_tags = set()
        expanded_tags_not_readable = set()

        # Add primary expanded tags
        for tag in augmented_page['tags']:
            assert tag.startswith('#'), 'invalid tag'
            expanded_tags_not_readable.add(tag)
            readable_tag = tag[1:].replace('_', ' ')
            expanded_tags.add(readable_tag)
        
        # Skip associated tags - vitD config.INCLUDE_ASSOCIATED_TAGS = False
        # Associated tags are too expansive, so we exclude them
        
        # Convert tags back to frontmatter format (remove # prefix, replace _ with spaces)
        final_tags = []
        for tag in augmented_page['tags']:
            if tag.startswith('#'):
                display_tag = tag[1:].replace('_', ' ')
                final_tags.append(display_tag)
            else:
                final_tags.append(tag)
        
        # Convert associated tags
        assoc_tags = []
        for tag in augmented_page['assoc_tags']:
            if tag.startswith('#'):
                display_tag = tag[1:].replace('_', ' ')
                assoc_tags.append(display_tag)
            else:
                assoc_tags.append(tag)
        
        # Update metadata with expanded tags - write back to "tags" field 
        metadata['tags'] = sorted(final_tags)
        if assoc_tags:
            metadata['associated_tags'] = sorted(assoc_tags)
        
        return {
            'file_path': file_path,
            'content': content,
            'metadata': metadata,
            'original_tags': categories,  # Original categories from frontmatter
            'expanded_tags': final_tags,
            'associated_tags': assoc_tags,
            'tags_added': len(final_tags) - len(categories)
        }
        
    except Exception as e:
        raise RuntimeError(f"❌ Failed to process markdown file {file_path}: {e}")


def write_processed_markdown(processed_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Write processed markdown data back to file with updated frontmatter
    FAIL FAST: Any write errors will raise exceptions immediately
    """
    if output_path is None:
        output_path = processed_data['file_path']
    
    try:
        # Create frontmatter post object
        post = frontmatter.Post(
            content=processed_data['content'],
            metadata=processed_data['metadata']
        )
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
        
        return output_path
        
    except Exception as e:
        raise RuntimeError(f"❌ Failed to write processed markdown to {output_path}: {e}")


def process_markdown_directory(directory_path: str, ontology_engine: OntologyEngine, 
                             pattern: str = "**/*.md") -> List[Dict[str, Any]]:
    """
    Process all markdown files in a directory using the ontology engine
    FAIL FAST: Any processing errors will raise exceptions immediately
    """
    import glob
    
    if not os.path.isdir(directory_path):
        raise NotADirectoryError(f"❌ Directory not found: {directory_path}")
    
    # Find all markdown files
    search_pattern = os.path.join(directory_path, pattern)
    markdown_files = glob.glob(search_pattern, recursive=True)
    
    if not markdown_files:
        print(f"⚠️  No markdown files found in {directory_path} with pattern {pattern}")
        return []
    
    print(f"Processing {len(markdown_files)} markdown files...")
    
    processed_files = []
    for file_path in markdown_files:
        try:
            processed_data = process_markdown_file(file_path, ontology_engine)
            processed_files.append(processed_data)
            
            if processed_data['tags_added'] > 0:
                print(f"✅ {os.path.basename(file_path)}: +{processed_data['tags_added']} tags")
            else:
                print(f"✅ {os.path.basename(file_path)}: no new tags")
                
        except Exception as e:
            print(f"❌ Failed to process {file_path}: {e}")
            raise  # FAIL FAST
    
    print(f"✅ Processed {len(processed_files)} markdown files")
    return processed_files


def analyze_tag_expansion(processed_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze the results of tag expansion across multiple files
    """
    if not processed_files:
        return {'total_files': 0}
    
    total_files = len(processed_files)
    total_original_tags = 0
    total_expanded_tags = 0
    total_associated_tags = 0
    
    all_original_tags = set()
    all_expanded_tags = set()
    all_associated_tags = set()
    
    files_with_expansion = 0
    
    for file_data in processed_files:
        original_count = len(file_data['original_tags'])
        expanded_count = len(file_data['expanded_tags'])
        associated_count = len(file_data['associated_tags'])
        
        total_original_tags += original_count
        total_expanded_tags += expanded_count
        total_associated_tags += associated_count
        
        all_original_tags.update(file_data['original_tags'])
        all_expanded_tags.update(file_data['expanded_tags'])
        all_associated_tags.update(file_data['associated_tags'])
        
        if expanded_count > original_count:
            files_with_expansion += 1
    
    return {
        'total_files': total_files,
        'files_with_expansion': files_with_expansion,
        'expansion_rate': files_with_expansion / total_files if total_files > 0 else 0,
        'total_original_tags': total_original_tags,
        'total_expanded_tags': total_expanded_tags,
        'total_associated_tags': total_associated_tags,
        'avg_original_tags_per_file': total_original_tags / total_files if total_files > 0 else 0,
        'avg_expanded_tags_per_file': total_expanded_tags / total_files if total_files > 0 else 0,
        'avg_associated_tags_per_file': total_associated_tags / total_files if total_files > 0 else 0,
        'unique_original_tags': len(all_original_tags),
        'unique_expanded_tags': len(all_expanded_tags),
        'unique_associated_tags': len(all_associated_tags),
        'expansion_factor': total_expanded_tags / total_original_tags if total_original_tags > 0 else 0
    }


def print_expansion_analysis(analysis: Dict[str, Any]):
    """Print tag expansion analysis in a readable format"""
    print("\n" + "="*60)
    print("TAG EXPANSION ANALYSIS")
    print("="*60)
    
    print(f"Files processed: {analysis['total_files']}")
    print(f"Files with tag expansion: {analysis['files_with_expansion']} ({analysis['expansion_rate']:.1%})")
    print()
    
    print(f"Total original tags: {analysis['total_original_tags']}")
    print(f"Total expanded tags: {analysis['total_expanded_tags']}")
    print(f"Total associated tags: {analysis['total_associated_tags']}")
    print()
    
    print(f"Average original tags per file: {analysis['avg_original_tags_per_file']:.1f}")
    print(f"Average expanded tags per file: {analysis['avg_expanded_tags_per_file']:.1f}")
    print(f"Average associated tags per file: {analysis['avg_associated_tags_per_file']:.1f}")
    print()
    
    print(f"Unique original tags: {analysis['unique_original_tags']}")
    print(f"Unique expanded tags: {analysis['unique_expanded_tags']}")
    print(f"Unique associated tags: {analysis['unique_associated_tags']}")
    print()
    
    print(f"Tag expansion factor: {analysis['expansion_factor']:.2f}x")
    print("="*60)


# Example usage and testing
if __name__ == "__main__":
    import sys
    
    # Test with ontology file
    ontology_file = "ontology.txt"
    
    try:
        # Load ontology engine
        print("Loading ontology engine...")
        engine = load_ontology_engine(ontology_file)
        
        # Test with a sample markdown file (if provided)
        if len(sys.argv) > 1:
            test_file = sys.argv[1]
            print(f"\nProcessing test file: {test_file}")
            
            processed = process_markdown_file(test_file, engine)
            
            print(f"\nOriginal tags: {processed['original_tags']}")
            print(f"Expanded tags: {processed['expanded_tags']}")
            print(f"Associated tags: {processed['associated_tags']}")
            print(f"Tags added: {processed['tags_added']}")
        
        else:
            print("\nUsage: python tag_processor.py <markdown_file>")
            print("Or call functions programmatically")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)