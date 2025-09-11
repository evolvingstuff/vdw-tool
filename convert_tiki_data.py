#!/usr/bin/env python3
"""
TikiWiki to Markdown Conversion Action
Ported from vitD main.py with FAIL FAST philosophy
"""

import csv
import json
import os
import datetime
from typing import List, Dict
import sys

import utils.slugs

# Add utils to path for imports
utils_path = os.path.join(os.path.dirname(__file__), '..', 'utils')
sys.path.append(utils_path)

import config
from utils import titles
from utils.models import Page, Category, Attachment
from utils.conversion_utils import convert_tiki_to_md
from utils.slugs import (
    generate_post_slug,
    create_post_slugs,
    generate_tiki_wiki_slug
)
from utils.blacklist import is_blacklisted
import utils.vitd_utils.globals as globals


def load_pages(cat_id_to_cat: Dict[int, Category]) -> Dict[int, Page]:
    """Load pages from JSON file - ported from vitD main.py"""
    print('Loading pages from JSON...')
    
    if not os.path.exists(config.PATH_TIKI_PAGES):
        raise FileNotFoundError(f"❌ TikiWiki pages file not found: {config.PATH_TIKI_PAGES}")
    
    with open(config.PATH_TIKI_PAGES, 'r') as f:
        entries = json.load(f)

    # Remove blacklisted pages
    temp = []
    removed = 0
    for entry in entries:
        if is_blacklisted(entry['pageName']):
            print(f"Skipping blacklisted page: {entry['pageName']}")
            removed += 1
            continue
        temp.append(entry)
    entries = temp

    if config.LIMIT_PROCESSING:
        entries = entries[config.PROCESSING_START:config.PROCESSING_END]

    if len(entries) == 0:
        raise ValueError("❌ No entries to process after filtering")

    # Create the post slugs before any parsing
    create_post_slugs(entries)

    pages: Dict[int, Page] = {}
    failed_pages = []
    
    for e, entry in enumerate(entries):
        page_id = entry['page_id']
        page_name = entry['pageName']
        print(f">> Processing page {page_id}: {page_name}")
        
        page_slug = entry['pageSlug']
        hugo_slug = generate_post_slug(page_name, False)
        
        if hugo_slug in config.MYSTERY_ERRORS:
            print(f'Skipping {hugo_slug} - in MYSTERY_ERRORS')
            failed_pages.append(entry)
            continue
            
        description = entry.get('description', None)
        hits = entry['hits']
        data_tiki = entry['data']

        try:
            data_md, censored_sections = convert_tiki_to_md(data_tiki)
            created = entry['created']
            last_modified = entry['lastModif']

            page = Page(
                page_id=page_id,
                page_name=page_name,
                page_slug=page_slug,
                description=description,
                hits=hits,
                data_tiki=data_tiki,
                data_md=data_md,
                created=created,
                last_modified=last_modified,
                censored_sections=censored_sections
            )
            
            if page_id in pages:
                raise ValueError(f"❌ Duplicate page_id {page_id}")
            pages[page_id] = page
            
        except Exception as e:
            print(f"❌ Failed to process page {page_id}: {page_name} - {e}")
            failed_pages.append((entry, str(e)))
            # FAIL FAST - uncomment next line to stop on first error
            # raise

    print(f'✅ Processed {len(pages)} pages')
    if failed_pages:
        path = 'errors.log'
        with open(path, 'w') as f:
            print(f'⚠️  Failed pages: {len(failed_pages)}')
            f.write(f'⚠️  Failed pages: {len(failed_pages)}\n')
            for i, failed_page in enumerate(failed_pages, 1):
                try:
                    print(f"\t[{i}]:\t{failed_page[0]['pageName']}")
                    f.write(f"\t[{i}]:\t{failed_page[0]['pageName']}\n")
                    f.write(f"\t\t\t{failed_page[1]}\n")
                except Exception as e:
                    print(f'WFT? {e}')

    if len(pages) == 0:
        raise ValueError("❌ No pages processed successfully")
    
    return pages


def load_categories() -> Dict[int, Category]:
    """Load categories from CSV - ported from vitD main.py"""
    print('Loading categories from CSV...')
    categories: Dict[int, Category] = {}
    names = set()

    # Load rosetta mapping for category name remapping
    rosetta_mapping = {}
    if os.path.exists(config.PATH_ROSETTA):
        with open(config.PATH_ROSETTA, mode='r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 3:
                    pre, post = row[1], row[2]
                    rosetta_mapping[pre] = post

    if not os.path.exists(config.PATH_CAT_ID_TO_NAME):
        raise FileNotFoundError(f"❌ Categories file not found: {config.PATH_CAT_ID_TO_NAME}")
        
    with open(config.PATH_CAT_ID_TO_NAME, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header
        for row in reader:
            if len(row) >= 2:
                id_str, name = row[0], row[1]
                # Apply rosetta mapping if available
                if name in rosetta_mapping:
                    name = rosetta_mapping[name]
                id_int = int(id_str)
                categories[id_int] = Category(cat_id=id_int, name=name)
                
                if name in names:
                    raise ValueError(f"❌ Duplicate category name: {name}")
                names.add(name)
                
    print(f'✅ Loaded {len(categories)} categories')
    return categories


def load_page_id_to_cat_ids() -> Dict[int, List[int]]:
    """Load page to category mappings - ported from vitD main.py"""
    print('Loading page to category mappings from CSV...')
    page_id_to_cat_id: Dict[int, List[int]] = {}
    valid, skipped = 0, 0
    
    if not os.path.exists(config.PATH_PAGE_ID_TO_CAT):
        print(f"⚠️  Page to category mapping file not found: {config.PATH_PAGE_ID_TO_CAT}")
        return page_id_to_cat_id
        
    with open(config.PATH_PAGE_ID_TO_CAT, mode='r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header
        for row in reader:
            if len(row) >= 5:
                page_id_str, cat_id_str = row[3], row[4]
                if page_id_str == '':
                    skipped += 1
                    continue
                page_id_int, cat_id_int = int(page_id_str), int(cat_id_str)
                if page_id_int not in page_id_to_cat_id:
                    page_id_to_cat_id[page_id_int] = []
                page_id_to_cat_id[page_id_int].append(cat_id_int)
                valid += 1
                
    print(f'✅ Loaded {valid} page-category mappings, skipped {skipped}')
    return page_id_to_cat_id


def load_att_id_to_file() -> Dict[int, Attachment]:
    """Load attachment mappings - ported from vitD main.py"""
    print('Loading attachments from JSON...')
    att_id_to_file: Dict[int, Attachment] = {}
    
    if not os.path.exists(config.PATH_TIKI_ATTACHMENTS):
        print(f"⚠️  Attachments file not found: {config.PATH_TIKI_ATTACHMENTS}")
        return att_id_to_file
        
    with open(config.PATH_TIKI_ATTACHMENTS, 'r') as jsonfile:
        js = json.load(jsonfile)
        for row in js:
            att_id_str, filename_str, filetype_str = row['attId'], row['filename'], row['filetype']
            att_id_int = int(att_id_str)
            if att_id_int in att_id_to_file:
                raise ValueError(f"❌ Duplicate attachment ID {att_id_int}")
            att_id_to_file[att_id_int] = Attachment(att_id=att_id_int, filename=filename_str, filetype=filetype_str)
            
    print(f'✅ Loaded {len(att_id_to_file)} attachments')
    return att_id_to_file


def generate_posts(page_id_to_page: Dict[int, Page],
                  cat_id_to_cat: Dict[int, Category],
                  page_id_to_cat_ids: Dict[int, List[int]]) -> List[tuple]:
    """Generate markdown posts with frontmatter - ported from vitD main.py"""
    print('Generating markdown posts...')
    
    posts = []
    to_process = sorted(page_id_to_page.keys())
    
    for page_id in to_process:
        original_title = page_id_to_page[page_id].page_name
        date = page_id_to_page[page_id].created
        
        # Convert Unix timestamp to YYYY-MM-DD format for Hugo
        try:
            date_obj = datetime.datetime.fromtimestamp(int(date))
            formatted_date = date_obj.strftime('%Y-%m-%d')
        except (ValueError, TypeError):
            formatted_date = '2000-01-01'  # Fallback date
            
        # Get categories for this page
        categories = []
        if page_id in page_id_to_cat_ids:
            for cat_id in page_id_to_cat_ids[page_id]:
                if cat_id in cat_id_to_cat:
                    categories.append(cat_id_to_cat[cat_id].name)

        # Process title (remove dates if configured)
        title = original_title
        if config.REMOVE_DATES_FROM_TITLES:
            title = titles.remove_dates_from_title_ends(title)
            
        # Generate slugs and aliases
        escaped_title = title.replace('"', '\\"')
        slug = generate_post_slug(title, False)
        escaped_slug = slug.replace('"', '\\"')
        
        # Generate alias using original title to preserve old URLs
        alias = generate_tiki_wiki_slug(original_title)
        escaped_alias = alias.replace('"', '\\"')
        escaped_categories = [cat.replace('"', '\\"') for cat in categories]

        # Generate JSON frontmatter (matching vitD format)
        aliases = []
        
        # Add TikiWiki-style alias if different from slug
        target_url = f'/posts/{escaped_slug}'
        tiki_alias = f'/{escaped_alias}'
        if tiki_alias != target_url and escaped_alias != escaped_slug:
            aliases.append(f"/{escaped_alias}")
            
        # Add page_id as alias
        aliases.append(f"/{page_id}")
        
        front_matter_dict = {
            "title": escaped_title,
            "slug": escaped_slug,
            "aliases": aliases,
            "tiki_page_id": page_id,
            "date": formatted_date,
            "censored_sections": page_id_to_page[page_id].censored_sections
        }
        
        if categories:
            front_matter_dict["categories"] = escaped_categories
            
        # Convert to JSON frontmatter
        front_matter_json = json.dumps(front_matter_dict, indent=2, separators=(',', ': '))
        front_matter = f"{front_matter_json}\n\n"
        
        # Create post
        filename = f'{slug}.md'
        data = page_id_to_page[page_id].data_md
        post = (filename, front_matter + data)
        posts.append(post)

    print(f'✅ Generated {len(posts)} markdown posts')
    return posts


def write_tiki_to_directory(pages, output_dir_tiki: str):
    """Write generated posts to output directory"""
    print(f'Writing tiki to {output_dir_tiki}...')

    # Create output directory if it doesn't exist
    os.makedirs(output_dir_tiki, exist_ok=True)

    # Clear existing posts
    for filename in os.listdir(output_dir_tiki):
        if filename.endswith('.tiki'):
            os.remove(os.path.join(output_dir_tiki, filename))

    for id in pages.keys():
        page = pages[id]
        slug = utils.slugs.generate_post_slug(page.page_name)
        path = os.path.join(output_dir_tiki, f'{slug}.tiki')
        with open(path, 'w') as outfile:
            outfile.write(page.data_tiki)

    print(f'✅ Wrote {len(pages.keys())} tiki to {output_dir_tiki}')


def write_posts_to_directory(posts: List[tuple], output_dir: str):
    """Write generated posts to output directory"""
    print(f'Writing posts to {output_dir}...')
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Clear existing posts
    for filename in os.listdir(output_dir):
        if filename.endswith('.md'):
            os.remove(os.path.join(output_dir, filename))
            
    # Write new posts
    for filename, content in posts:
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
            
    print(f'✅ Wrote {len(posts)} posts to {output_dir}')


def convert_tiki_data():
    """Main conversion function - FAIL FAST throughout"""
    print('🔄 Starting TikiWiki to Markdown conversion...')
    
    try:
        # Load attachment mappings into global variable (required by parser)
        globals.att_id_to_file = load_att_id_to_file()
        
        # Load categories and mappings
        cat_id_to_cat = load_categories()
        page_id_to_cat_ids = load_page_id_to_cat_ids()
        
        # Load and convert pages
        pages = load_pages(cat_id_to_cat)

        # write tiki to dir
        write_tiki_to_directory(pages, config.OUTPUT_DIR_TIKI)
        
        # Generate markdown posts
        posts = generate_posts(pages, cat_id_to_cat, page_id_to_cat_ids)
        
        # Write to output directory
        write_posts_to_directory(posts, config.OUTPUT_DIR)
        
        print('✅ TikiWiki to Markdown conversion completed successfully!')
        print(f'📁 Output written to: {config.OUTPUT_DIR} and {config.OUTPUT_DIR_TIKI}')
        
    except Exception as e:
        print(f'❌ Conversion failed: {e}')
        raise  # FAIL FAST


if __name__ == '__main__':
    convert_tiki_data()