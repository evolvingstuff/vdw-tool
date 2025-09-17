import config


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
    if title in config.BLACKLISTED_TITLES:
        return True

    # Check pattern matches
    for pattern in config.BLACKLIST_PATTERNS:
        if pattern.search(title):
            return True

    return False