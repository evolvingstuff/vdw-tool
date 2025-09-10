import re

import config

# TODO: add log of pages filtered using blacklist


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


def is_blacklisted(title: str) -> bool:
    """
    Check if a given title is blacklisted.
    Returns True if the title:
    - Matches exactly with BLACKLISTED_TITLES
    - Matches any of the blacklist patterns
    """
    if not config.APPLY_TITLE_BLACKLISTING:
        return False

    # Check exact matches
    if title in BLACKLISTED_TITLES:
        return True

    # Check pattern matches
    for pattern in BLACKLIST_PATTERNS:
        if pattern.search(title):
            return True

    return False