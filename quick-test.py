#!/usr/bin/env python3
"""
Quick TikiWiki to Markdown converter for testing
Allows pasting TikiWiki syntax and getting markdown output
"""

import sys
import os

# Add utils to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the conversion function and required modules
from utils.conversion_utils import convert_tiki_to_md
import utils.vitd_utils.globals as globals
from utils.models import Attachment
import config

def main():
    print("=== TikiWiki to Markdown Quick Test ===")
    print("Paste your TikiWiki content and press Enter:")
    print("-" * 40)

    # Read single paste operation
    tiki_content = input()

    # Replace literal \n with actual newlines (in case user pastes escaped content)
    tiki_content = tiki_content.replace('\\n', '\n')

    if not tiki_content.strip():
        print("\nNo content provided. Exiting.")
        sys.exit(1)

    print("\n" + "=" * 40)
    print("CONVERTING...")
    print("=" * 40 + "\n")

    try:
        # Initialize empty attachments dict (required by parser)
        globals.att_id_to_file = {}

        # Convert TikiWiki to Markdown
        markdown_output, sections_included, sections_excluded = convert_tiki_to_md(tiki_content)

        print("=== MARKDOWN OUTPUT ===")
        print(markdown_output)

        if config.DEBUG_MODE:
            print("\n=== DEBUG INFO ===")
            print(f"Sections included: {sections_included}")
            print(f"Sections excluded: {sections_excluded}")

    except Exception as e:
        print(f"\n❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()