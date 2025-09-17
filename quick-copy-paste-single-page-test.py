#!/usr/bin/env python3
"""
Quick TikiWiki to Markdown converter for testing
Allows pasting TikiWiki syntax and getting markdown output
"""

import sys
import os
import json
import select

# Add utils to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the conversion function and required modules
from utils.conversion_utils import convert_tiki_to_md
import utils.vitd_utils.globals as globals
from utils.models import Attachment
import config

def load_attachments_if_available():
    """Load attachment mappings if the file exists"""
    att_id_to_file = {}

    if os.path.exists(config.PATH_TIKI_ATTACHMENTS):
        try:
            with open(config.PATH_TIKI_ATTACHMENTS, 'r') as jsonfile:
                js = json.load(jsonfile)
                for row in js:
                    att_id = int(row['attId'])
                    filename = row['filename']
                    filetype = row['filetype']
                    att_id_to_file[att_id] = Attachment(att_id=att_id, filename=filename, filetype=filetype)
            print(f"✅ Loaded {len(att_id_to_file)} attachments")
        except Exception as e:
            print(f"⚠️  Could not load attachments: {e}")
    else:
        print(f"ℹ️  No attachments file found at {config.PATH_TIKI_ATTACHMENTS}")

    return att_id_to_file

def main():
    print("=== TikiWiki to Markdown Quick Test ===")

    # Load attachment mappings if available
    print("Loading data files...")
    globals.att_id_to_file = load_attachments_if_available()

    print("\nPaste your TikiWiki content below:")
    print("-" * 40)

    # Set stdin to non-blocking mode
    import fcntl
    fd = sys.stdin.fileno()
    flags = fcntl.fcntl(fd, fcntl.F_GETFL)
    fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)

    # Read ALL available input at once
    content = []
    empty_reads = 0

    while empty_reads < 3:  # After 3 empty reads (0.3 seconds), we're done
        try:
            # Check if input is available
            if select.select([sys.stdin], [], [], 0.1)[0]:
                # Read ALL available data in non-blocking mode
                try:
                    chunk = sys.stdin.read()
                    if chunk:
                        content.append(chunk)
                        empty_reads = 0
                    else:
                        empty_reads += 1
                except:
                    empty_reads += 1
            else:
                if content:
                    empty_reads += 1
                # Keep waiting if no content yet
        except:
            break

    tiki_content = ''.join(content)

    if not tiki_content.strip():
        print("\nNo content provided. Exiting.")
        sys.exit(1)

    print("\n" + "=" * 40)
    print("CONVERTING...")
    print("=" * 40 + "\n")

    try:
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