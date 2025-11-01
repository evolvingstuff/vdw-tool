import re
import unicodedata
from typing import Dict
import config
import utils.titles

unique_post_slugs = set()
post_slug_counter: Dict[str, int] = {}

unique_category_slugs = set()
# category_slug_counter: Dict[str, int] = {}

post_slugs_that_exist = set()
tag_slugs_that_exist = set()


def generate_post_slug(title: str, enforce_unique: bool = False) -> str:
    """
    Generates a unique slug from the given title.

    The function:
    1. Converts to lowercase
    2. Normalizes unicode characters
    3. Removes special characters
    4. Replaces spaces with hyphens
    5. Ensures uniqueness by adding a suffix if needed

    Args:
        title: The title to convert to a slug

    Returns:
        A unique slug string
    """
    if not title:
        raise ValueError("Title cannot be empty")

    if config.REMOVE_DATES_FROM_TITLES:
        title = utils.titles.remove_dates_from_title_ends(title)  # sometimes redundant but needed for local links...

    # Convert to lowercase and normalize unicode
    slug = title.lower()
    slug = unicodedata.normalize('NFKD', slug).encode('ascii', 'ignore').decode('ascii')

    special = {
        '%': '  percent'
    }

    for key in special.keys():
        slug = slug.replace(key, special[key])

    # Remove special characters and replace spaces with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    slug = slug.strip('-')
    while '--' in slug:
        slug = slug.replace('--', '-')

    # Ensure slug is not too long (most web servers have URL length limits)
    if len(slug) > 100:
        # Keep the beginning and end parts for context, but truncate the middle
        slug = slug[:80] + "-" + slug[-15:]

    # Ensure uniqueness
    if enforce_unique:
        base_slug = slug
        # Count occurrences; the first occurrence should be kept as-is (no suffix),
        # the second occurrence should use "-2", then "-3", etc. Never "-1".
        count = post_slug_counter.get(base_slug, 0) + 1
        post_slug_counter[base_slug] = count
        if count == 1:
            # First occurrence gets the base slug
            slug = base_slug
        else:
            # Subsequent occurrences get -2, -3, ...
            slug = f"{base_slug}-{count}"
        unique_post_slugs.add(slug)
        
        # Check for overlap between post and category slug sets
        intersection = unique_post_slugs.intersection(unique_category_slugs)
        if intersection:
            raise ValueError(f"Found overlapping slugs between posts and categories: {intersection}")
    
    return slug


def generate_tiki_wiki_slug(title: str) -> str:
    """
    Generates a Tiki Wiki style slug from a title.

    Features:
    - Preserves capital letters
    - Replaces spaces with + signs
    - Removes most special characters
    - Preserves certain special characters like – (en dash)

    Args:
        title: The title to convert to a Tiki Wiki style slug

    Returns:
        A string in the Tiki Wiki slug format
    """
    if not title:
        return ""

    # Normalize unicode characters
    slug = unicodedata.normalize('NFKD', title)

    # Replace spaces with + signs
    slug = slug.replace(' ', '+')

    # Remove certain special characters but keep others
    # Keep: letters, numbers, plus signs, and dashes
    slug = re.sub(r'[^\w\+\-–]', '', slug)

    # Remove consecutive plus signs
    slug = re.sub(r'\++', '+', slug)

    # Remove plus signs from start and end
    slug = slug.strip('+')

    return slug


def generate_hugo_category_slug(category_name: str) -> str:
    """
    Generates a slug for categories that matches Hugo's default category URL slugification.
    
    Unlike our custom generate_slug, this preserves punctuation and only:
    1. Converts to lowercase
    2. Replaces spaces with hyphens
    
    Args:
        category_name: The category name to convert to a Hugo-style slug
        
    Returns:
        A slug string matching Hugo's default behavior for categories
    """
    if not category_name:
        raise ValueError("Category name cannot be empty")
        
    # Convert to lowercase and replace spaces with hyphens
    # Hugo preserves most punctuation in category slugs
    slug = category_name.lower().replace(' ', '-')
    
    return slug


def generate_hugo_tag_slug(tag_name: str) -> str:
    """
    Generates a slug for tags that matches Hugo's default tag URL slugification.
    
    Hugo converts tag names to lowercase and replaces spaces and special characters
    with hyphens for URL-safe slugs.
    
    Args:
        tag_name: The tag name to convert to a slug
        
    Returns:
        A slug string matching Hugo's default behavior for tags
    """
    if not tag_name:
        return config.unknown_tag
    
    # Convert underscores and slashes to spaces first, then to dashes for consistent normalization
    # This handles both "Vitamin D" -> "vitamin-d", "vitamin_d" -> "vitamin-d", and
    # "Amyotrophic Lateral Sclerosis/ALS" -> "amyotrophic-lateral-sclerosis-als"
    normalized = tag_name.replace('_', ' ').replace('/', ' ')
    
    # Convert to lowercase and replace spaces/special chars with hyphens
    slug = re.sub(r'[^\w\s-]', '', normalized.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    
    if not slug:
        # raise ValueError(f"Tag name '{tag_name}' resulted in empty slug")
        return config.unknown_tag

    return slug


def generate_category_link(category_name: str) -> str:
    """
    Generates a complete markdown link for a category.
    
    Args:
        category_name: The name of the category
        
    Returns:
        A formatted markdown link: [Category Name](/categories/category-slug/)
    """
    slug = generate_hugo_category_slug(category_name)
    return f"[{category_name}](/categories/{slug}/)"


def generate_tag_link(tag_name: str) -> str:
    """
    Generate a markdown link to a tag page.
    
    Args:
        tag_name: The name of the tag
        
    Returns:
        A formatted markdown link: [Tag Name](/tags/tag-slug/)
    """
    slug = generate_hugo_tag_slug(tag_name)
    return f"[{tag_name}](/tags/{slug}/)"


def create_post_slugs(entries):
    """Create post slugs for all entries to track existence (derived from pageName)."""
    print('Creating post slugs...')
    for entry in entries:
        slug = generate_post_slug(entry['pageName'], enforce_unique=False)
        post_slugs_that_exist.add(slug)
    print(f'Created {len(post_slugs_that_exist)} post slugs')


def precompute_page_maps(entries):
    """Precompute unique slugs and page mappings for all entries.

    - Ensures unique slugs by appending -1, -2, ... when needed.
    - Populates config maps:
        * map_page_id_to_page_name
        * map_page_name_to_page_id
        * map_page_id_to_page_slug
        * map_page_name_to_page_slug
    - Populates post_slugs_that_exist with the unique slugs.
    """
    print('Precomputing unique page slugs and page maps...')

    # Reset internal uniqueness tracking and existence set
    unique_post_slugs.clear()
    post_slug_counter.clear()
    post_slugs_that_exist.clear()

    # Reset mapping containers
    config.map_page_id_to_page_name.clear()
    config.map_page_name_to_page_id.clear()
    config.map_page_id_to_page_slug.clear()
    config.map_page_name_to_page_slug.clear()

    for entry in entries:
        page_id = entry['page_id']
        page_name = entry['pageName']

        # Update id<->name maps
        config.map_page_id_to_page_name[page_id] = page_name
        config.map_page_name_to_page_id[page_name] = page_id

        # Compute unique slug from page name
        slug = generate_post_slug(page_name, enforce_unique=True)

        # Register slug
        post_slugs_that_exist.add(slug)
        config.map_page_id_to_page_slug[page_id] = slug
        config.map_page_name_to_page_slug[page_name] = slug

    print(f'✅ Precomputed {len(post_slugs_that_exist)} unique slugs')


def create_tag_slugs_from_posts(all_tags_set):
    """
    Create tag slugs from a set of all tags found in posts.
    This will be called from the Hugo processing after collecting all tags.
    """
    print('creating tag slugs...')
    for tag in all_tags_set:
        slug = generate_hugo_tag_slug(tag)
        tag_slugs_that_exist.add(slug)
    print(f'Created {len(tag_slugs_that_exist)} tag slugs')
