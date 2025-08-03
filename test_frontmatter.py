#!/usr/bin/env python3
"""
Test frontmatter behavior with JSON vs YAML
"""
import sys
sys.path.append('_src/utils')

import frontmatter

# Test with the actual markdown file
test_file = "posts/1000-iu-vitamin-d-did-not-reduce-cardiovascular-risk-factors.md"

print("=== TESTING FRONTMATTER BEHAVIOR ===")
print(f"Reading: {test_file}")

# Load the file
with open(test_file, 'r', encoding='utf-8') as f:
    post = frontmatter.load(f)

print(f"Metadata keys: {list(post.metadata.keys())}")
print(f"Title: {post.metadata.get('title', 'N/A')}")

# Test what dumps() produces
output = frontmatter.dumps(post)
print("\n=== FRONTMATTER.DUMPS() OUTPUT ===")
print(output[:500] + "..." if len(output) > 500 else output)

# Check if it starts with { (JSON) or --- (YAML)
first_char = output.strip()[0] if output.strip() else 'EMPTY'
print(f"\nFirst character: '{first_char}'")
print(f"Format appears to be: {'JSON' if first_char == '{' else 'YAML' if output.strip().startswith('---') else 'UNKNOWN'}")