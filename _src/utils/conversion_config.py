NO_TABLE_HEADERS = True
LOOSE_RENDERING = False
DOUBLE_TEXT_NODE_NEWLINES = True
REMOVE_DATES_FROM_TITLES = True
REMOVE_DOUBLE_SQUARE_BRACKETS = True
USE_SEARCH_COMPRESSION = True
REMOVE_NON_COMPRESSED_FILES = True
REMOVE_PADDING = True  # remove leading whitespace from lines before parsing
REDUCE_TRIPLE_PARENS = True
ADD_MISSING_BRACKET_ON_LEFT = True
TRANSFORM_DISPLAY_XXXX = True
ADD_HTML_COMMENTS_FOR_HIDDEN_NODES = True
ADD_HTML_COMMENTS_DURING_POST_CENSOR = False
RENDER_TOC = True
DEBUG_COLOR = False
DEBUG_DOI = False
REPLACE_ASTERISKS_INSIDE_HTML = True
ASTERISK_REPLACEMENT = '✻'  # '✱'
# VDW Tool paths - adjust for project structure
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go up to project root
DATA_DIR = os.path.join(BASE_DIR, 'data')
OUTPUT_DIR = os.path.join(BASE_DIR, 'posts')

PATH_TIKI_PAGES = os.path.join(DATA_DIR, '_src_files', 'tiki_pages_2025-05-04.json')
PATH_TIKI_CATEGORIES = os.path.join(DATA_DIR, '_src_files', 'tiki_categories_2025-05-04.json')
PATH_TIKI_ATTACHMENTS = os.path.join(DATA_DIR, '_src_files', 'tiki_wiki_attachments_2025-05-04.json')
PATH_CAT_ID_TO_NAME = os.path.join(DATA_DIR, 'catId-to-catName.csv')
PATH_PAGE_ID_TO_CAT = os.path.join(DATA_DIR, 'pageId-to-catId.csv')
PATH_ROSETTA = os.path.join(DATA_DIR, 'rosetta.csv')

COPY_ATTACHMENTS = False
path_tiki_attachments = PATH_TIKI_ATTACHMENTS
FRONT_MATTER_FORMAT = 'json'  # json | yaml
INCLUDE_ASSOCIATED_TAGS = False  # Whether to include associated tags from ontology in page tags
###################
POST_CENSOR = True
REMOVE_VITAMIN_D_WIKI_DASH_PREFIX = True
BLACKLIST = [
    '{include',
    '{SQL',
    '{LIST()',
    '{category',
    '{LISTPAGES',
    'in the title',
    'VitaminDWiki - ',
    'VitaminDWiki – '
]
# BLACKLIST = []

# 0 - 5000 yes
# 2500 - 5000 yes
# 4000 - 5000 yes
MYSTERY_ERRORS = [
    'fix-thyroid-then-increase-vitamin-d'
]
USE_PAGEFIND_YAML = False  # not working yet
CLOUDFRONT_URL = 'https://d378j1rmrlek7x.cloudfront.net' # 'https://d1bk1kqxc0sym.cloudfront.net'

########
LIMIT_PROCESSING = True
PROCESSING_START = 2500  # 2500
PROCESSING_END = 10000  # -1  # -343  # this is the boundary for the last page to process
DEBUG_MODE = False  # shows tiki data underneath markdown data
STATIC_SITE_DIR = '../vdw2'  # '../vitaminDWiki_static_site'
