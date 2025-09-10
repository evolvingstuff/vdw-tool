def remove_dates_from_title_ends(title):
    """
    * May or may not have dash
    * Full or abbreviated month

    Examples:

    Autism risky if low vitamin D during pregnancy and early life (mice, fecal transplant reversed it) – March 2024
    Monthly vitamin D dosing better for children than daily (again) - Oct 2023
    Gestational Diabetes best fought by Vitamin D plus probiotics – RCT review Dec 2023
    Microencapsulated Vitamin D better than oil-based in 6 ways – Sept 2023
    """
    import re
    
    # Pattern for detecting dates at the end of titles
    # This covers:
    # - Optional dash or en-dash followed by spaces
    # - Full month names and all common abbreviations
    # - Optional spaces and day number
    # - Optional comma
    # - Required year (2 or 4 digits)
    date_pattern = r'(?:[-–—]\s*)?(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t)?(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s*(?:\d{1,2},?\s*)?(?:19|20)?\d{2}\s*$'
    
    # Remove the date pattern if it exists at the end of the title
    cleaned_title = re.sub(date_pattern, '', title, flags=re.IGNORECASE)
    
    # Trim any trailing whitespace
    cleaned_title = cleaned_title.rstrip()
    
    # Also remove any trailing dash that might be left after removing the date
    cleaned_title = re.sub(r'[-–—]\s*$', '', cleaned_title)
    
    # Final trim of whitespace
    return cleaned_title.rstrip()