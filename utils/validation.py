import re
from typing import Optional

def validate_person_name(name: str) -> bool:
    """
    Validate person name format
    
    Args:
        name: Person's name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not name or not isinstance(name, str):
        return False
    
    # Remove extra whitespace
    name = name.strip()
    
    # Check minimum length
    if len(name) < 2:
        return False
    
    # Check maximum length
    if len(name) > 100:
        return False
    
    # Check for valid characters (letters, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
        return False
    
    # Check for at least one letter
    if not re.search(r'[a-zA-Z]', name):
        return False
    
    # Split into words and validate
    words = name.split()
    
    # Should have at least one word
    if len(words) < 1:
        return False
    
    # Each word should have at least one character
    for word in words:
        if len(word.strip()) < 1:
            return False
    
    return True

def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_url(url: str) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # Basic URL regex pattern
    pattern = r'^https?://(?:[-\w.])+(?::\d+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?$'
    return bool(re.match(pattern, url))

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    Sanitize user input
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
    """
    if not text or not isinstance(text, str):
        return ""
    
    # Remove extra whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    # Remove potentially dangerous characters
    # Keep only alphanumeric, spaces, and common punctuation
    text = re.sub(r'[^\w\s\-.,;:!?()\'"@#$%&*+=]', '', text)
    
    return text

def validate_search_query(query: str) -> bool:
    """
    Validate search query
    
    Args:
        query: Search query to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not query or not isinstance(query, str):
        return False
    
    # Remove extra whitespace
    query = query.strip()
    
    # Check minimum length
    if len(query) < 2:
        return False
    
    # Check maximum length
    if len(query) > 500:
        return False
    
    # Should contain at least one alphanumeric character
    if not re.search(r'[a-zA-Z0-9]', query):
        return False
    
    return True

def extract_name_parts(full_name: str) -> dict:
    """
    Extract name parts from full name
    
    Args:
        full_name: Full name string
        
    Returns:
        Dictionary with name parts
    """
    if not validate_person_name(full_name):
        return {}
    
    # Clean the name
    name = full_name.strip()
    
    # Split into parts
    parts = name.split()
    
    # Handle different name formats
    if len(parts) == 1:
        return {
            'first_name': parts[0],
            'middle_name': '',
            'last_name': ''
        }
    elif len(parts) == 2:
        return {
            'first_name': parts[0],
            'middle_name': '',
            'last_name': parts[1]
        }
    elif len(parts) == 3:
        return {
            'first_name': parts[0],
            'middle_name': parts[1],
            'last_name': parts[2]
        }
    else:
        # More than 3 parts - combine middle parts
        return {
            'first_name': parts[0],
            'middle_name': ' '.join(parts[1:-1]),
            'last_name': parts[-1]
        }

def normalize_name(name: str) -> str:
    """
    Normalize name for consistent processing
    
    Args:
        name: Name to normalize
        
    Returns:
        Normalized name
    """
    if not name or not isinstance(name, str):
        return ""
    
    # Remove extra whitespace and convert to title case
    normalized = ' '.join(name.strip().split()).title()
    
    # Handle common prefixes and suffixes
    prefixes = ['Dr.', 'Mr.', 'Mrs.', 'Ms.', 'Prof.', 'Sr.', 'Jr.']
    suffixes = ['Jr.', 'Sr.', 'II', 'III', 'IV', 'V']
    
    # This is a simple normalization - could be enhanced
    return normalized

def validate_date_string(date_str: str) -> bool:
    """
    Validate date string format
    
    Args:
        date_str: Date string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not date_str or not isinstance(date_str, str):
        return False
    
    # Common date patterns
    patterns = [
        r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
        r'^\d{2}/\d{2}/\d{4}$',  # MM/DD/YYYY
        r'^\d{2}-\d{2}-\d{4}$',  # MM-DD-YYYY
        r'^\d{4}$',              # YYYY only
    ]
    
    for pattern in patterns:
        if re.match(pattern, date_str):
            return True
    
    return False