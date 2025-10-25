import re

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
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))  # Go up to project root
# DATA_DIR = os.path.join(BASE_DIR, 'data')
# OUTPUT_DIR = os.path.join(BASE_DIR, 'posts')

DATA_DIR = '../vdw-external-data'
OUTPUT_DIR = '../vdw-posts/posts'
OUTPUT_DIR_TIKI = '../vdw-posts/posts_tiki'

PATH_TIKI_PAGES = os.path.join(DATA_DIR, '_src_files', 'tiki_pages_2025-10-03.json')
PATH_TIKI_CATEGORIES = os.path.join(DATA_DIR, '_src_files', 'tiki_categories_2025-10-03.json')
PATH_TIKI_ATTACHMENTS = os.path.join(DATA_DIR, '_src_files', 'tiki_wiki_attachments_2025-10-24.json')
PATH_TIKI_FILES = os.path.join(DATA_DIR, '_src_files', 'tiki_files_2025-10-24.json')
PATH_ROSETTA = os.path.join(DATA_DIR, 'rosetta.csv')

# TODO asdf
PATH_CAT_ID_TO_NAME = os.path.join(DATA_DIR, 'catId-to-catName.csv')
PATH_PAGE_ID_TO_CAT = os.path.join(DATA_DIR, 'pageId-to-catId.csv')


COPY_ATTACHMENTS = False
path_tiki_attachments = PATH_TIKI_ATTACHMENTS
FRONT_MATTER_FORMAT = 'json'  # json | yaml
INCLUDE_ASSOCIATED_TAGS = False  # Whether to include associated tags from ontology in page tags
###################
# TODO: we should have all of the blacklists in one place...
BLACKLISTED_SECTIONS = [
    '{include',
    '{SQL',
    '{LIST()',
    '{category',
    '{LISTPAGES',
    # 'in the title',
    # 'VitaminDWiki - ',
    # 'VitaminDWiki – '
]
BLACKLISTED_TITLES = {
    "Wiki Help",
    "Registered HomePage",
    "Instructions",
    "Community",
    "New pages",
    "Moved76",
    "removed2",
    "HelpOpenFiles"
    "HelpSize",
    "VDWMostViewed",
    "list pages",
    "PagesFiles",
    "ShowPages",
    "iPadTips",
    "MakeASimplePage",
    "GoogleTranslate",
    "ScreenMagnification",
    "Tet of getting Toc of another page",
    "interactive pdf test",
    "Tiki reference material",
    "top 1000 most visited",
    "search_smartmenu_dropdown",
    "Paywall in title",
    "Test Meta-analysis",
    # "Transcripts in VitaminDWiki",
    # "Top Vitamin D",
    # "Cancer - Liver",
    # "Deficiency of Vitamin D",
    # "Food sources for Vitamin D",
    # "Interactions with Vitamin D",
    # "Vitamin D in the Middle East",
    # "Vitamin D far from the Equator",
    # "Vitamin D in Canada",
    # "Vitamin D and Vitiman A",
    # "Vitamin D3 instead of D2",
    # "Tests for Vitamin D",
    # "Fortification with Vitamin D",
    # "UV and Vitamin D",
    # "Toxicity of Vitamin D",
    # "Vitamin D and Vitamin K",
    # "Vitamin D and Omega-3",
    # "Vitamin D and Magnesium",
    # "Vitamin D and Calcium",
    # "Diseases TREATED by Vitamin D",
    # "Sun and Vitamin D",
    # "Loading dose for Vitamin D",
    # "UV and D",
    # "Veterinary and D",
    # "Health",
    # "Overviews",
    # "Hypertension",
    # "Immunity",
    "Sample Category Page",
    "Search other sites",
    "Test WYSIYWG",
    "Suggestions on how to record a meeting",
    "Moved 60",
    "Rick's Test Page",
    # "Medline and vitamin D",
    "Google Translate of VitaminDWiki",
    # ". Vitamin D",
    # "Vaccine vs vitamin D",
    # "Tinnitus and vitamin D",
    # "Popular Pages",
    "Searching Vitamin D Wiki",
}
# Compile regex patterns for efficiency
BLACKLIST_PATTERNS = [
    re.compile(r'^moved\d+$', re.IGNORECASE),
    re.compile(r'^removed\d+$', re.IGNORECASE),
    # Match CamelCase/PascalCase pattern: word starting with capital followed by
    # at least one more capitalized word
    re.compile(r'^[A-Z][a-z]+([A-Z][a-z]+)+$'),
    # Match "test page" at start of title, case insensitive
    re.compile(r'^test '),
    # Match any word immediately followed by number(s), e.g. "Junk6"
    re.compile(r'^[a-zA-Z]+\d+$'),
    # Match titles starting with "redirected "
    re.compile(r'^redirected ', re.IGNORECASE),
    # Match titles ending with " most visited"
    re.compile(r' most visited$', re.IGNORECASE),
    # Match words connected by underscores (2 or more words)
    re.compile(r'^[a-zA-Z]+(_[a-zA-Z]+)+$'),
    # Match titles starting with lowercase letter
    re.compile(r'^[a-z]'),
    # Match titles containing "(test)"
    re.compile(r'\(test\)', re.IGNORECASE),
    # Match titles starting with "Test: "
    re.compile(r'^test: ', re.IGNORECASE),
    # # Match single-word titles
    # re.compile(r'^[A-Za-z]+$'),
    # Match titles containing "Tiki"
    re.compile(r'tiki', re.IGNORECASE)
]

# 0 - 5000 yes
# 2500 - 5000 yes
# 4000 - 5000 yes
MYSTERY_ERRORS = [
    'fix-thyroid-then-increase-vitamin-d'
]
USE_PAGEFIND_YAML = False  # not working yet
# TODO move to .env
CLOUDFRONT_URL = 'https://d378j1rmrlek7x.cloudfront.net' # 'https://d1bk1kqxc0sym.cloudfront.net'

########
LIMIT_PROCESSING = False
PROCESSING_START = -200  # 2500
PROCESSING_END = None  # -1  # -343  # this is the boundary for the last page to process
DEBUG_MODE = False  # shows tiki data underneath markdown data

########################################
APPLY_TITLE_BLACKLISTING = False  # True
POST_CENSOR = False  # True
