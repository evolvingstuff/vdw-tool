import re
import os
from typing import Set, Dict


def sanitize_filename(name: str) -> str:
    """
    Sanitize a filename to be safe for filesystem and URL usage.
    Converts to lowercase, replaces spaces with underscores,
    and ensures only alphanumeric, underscores, hyphens and periods remain.
    
    Args:
        name: The original filename to sanitize
        
    Returns:
        A sanitized version of the filename
    """
    # Convert to lowercase for consistency
    sanitized = name.lower()
    
    # Replace spaces with underscores
    sanitized = sanitized.replace(' ', '_')
    
    # Replace any non-allowed characters with underscores
    # Allow: alphanumeric, underscore, hyphen, and period
    sanitized = re.sub(r'[^a-z0-9_\-\.]', '_', sanitized)
    
    # Replace consecutive underscores with a single underscore
    sanitized = re.sub(r'_+', '_', sanitized)

    sanitized = sanitized.replace('_', '-')
    
    # Ensure we don't end up with an empty string
    if not sanitized:
        sanitized = "unnamed_file"
    
    return sanitized
