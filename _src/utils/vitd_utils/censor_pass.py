import re
from typing import List

import conversion_config as config

def break_into_sections(md: str) -> List[str]:
    # Validate input
    if not isinstance(md, str):
        raise ValueError(f"Expected string input, got {type(md).__name__}")
    
    if not md:
        raise ValueError("Input markdown content is empty")
    
    # The pattern for section delimiter: newline, three or more dashes, newline
    section_pattern = r'\n-{3,}\n'
    
    # Handle special case: if the content starts with a delimiter
    if md.startswith('---\n'):
        md = md[4:]  # Remove the starting delimiter
    
    # Split by the section delimiter pattern
    sections = re.split(section_pattern, md)
    
    # Validate that we got sensible output
    if not sections:
        # print(f"DEBUG: No sections found in content: '{md[:100]}...'")
        # Return the whole content as a single section if no delimiters found
        return [md]
    
    return sections


def process_section(section: str) -> str:
    # Validate input
    if not isinstance(section, str):
        raise ValueError(f"Expected string input, got {type(section).__name__}")
    
    # If section is empty, return it as is
    if not section:
        return section

    # censor if ANY line
    for blacklisted in config.BLACKLIST:
        if blacklisted.lower() in section.lower():
            return '\n\n'
    return section


def post_censor(md: str) -> str:

    sections: List[str] = break_into_sections(md)
    
    # print(f"DEBUG: Found {len(sections)} sections")

    processed_sections: List[str] = []

    for i, section in enumerate(sections):
        # Process the section first
        processed_section = process_section(section)
        
        # Get stripped content of original and processed section for debugging
        proc_stripped = processed_section.strip()
        
        # Check if the processed section is effectively empty:
        # - Empty string
        # - Only whitespace
        # - Only HTML comments (<!-- ... -->)
        is_empty = not processed_section or processed_section.isspace()
        
        # If not obviously empty, check if it contains only HTML comments
        if not is_empty and proc_stripped.startswith('<!--') and proc_stripped.endswith('-->'):
            # Remove HTML comments and check if anything meaningful remains
            comment_removed = re.sub(r'<!--.*?-->', '', processed_section, flags=re.DOTALL)
            is_empty = not comment_removed.strip()
        
        if is_empty:
            # print(f"DEBUG: Skipping effectively empty section #{i} (original length: {len(section)})")
            # print(f"DEBUG: Original content (first 50 chars): '{orig_stripped[:50]}'")
            # print(f"DEBUG: Processed content (first 50 chars): '{proc_stripped[:50]}'")
            continue
            
        # Only add non-blank processed sections
        processed_sections.append(processed_section)

    # print(f"DEBUG: After processing, {len(processed_sections)} non-empty sections remain")
    processed_md = '\n---\n'.join(processed_sections)

    return processed_md