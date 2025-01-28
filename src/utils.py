"""
Utility functions for the AI News Scraper
Contains helper functions used across the application
"""

from datetime import datetime
import logging


def safe_str(value):
    """
    Convert any value to string safely.
    
    Args:
        value: Any value to be converted to string
        
    Returns:
        str: String representation of the value or empty string if None
    """
    if value is None:
        return ""
    return str(value)

def parse_article_date(date_str):
    """
    Converts a date string into a standardized date object.

    Args:
        date_str (str): Date string to parse

    Returns:
        date: Parsed date object or None if parsing fails
    """
    formats = ['%d %B %Y', '%Y-%m-%d', '%B %d, %Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    logging.warning(f"Unrecognized date format: {date_str}")
    return None

def setup_http_session():
    """
    Sets up an HTTP session with retry logic.
    
    Returns:
        requests.Session: Configured session object
    """
    from requests import Session
    from requests.adapters import HTTPAdapter
    from requests.packages.urllib3.util.retry import Retry
    
    session = Session()
    retries = HTTPAdapter(max_retries=5)
    session.mount('http://', retries)
    session.mount('https://', retries)
    
    return session