"""
Utility functions for the AI News Scraper
Contains helper functions used across the application
"""

from datetime import datetime
import logging
import os

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


def setup_logging(log_level=logging.INFO):
    """
    Set up logging configuration for the entire application
    
    Args:
        log_level: Logging level (default: INFO)
    
    Returns:
        Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create timestamped log filename
    log_filename = os.path.join(log_dir, f"ai_news_scraper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
    
    # Configure logging
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            # File handler for persistent logs
            logging.FileHandler(log_filename),
            # Stream handler for console output
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger('ai_news_scraper')
    
    logger.info(f"Logging configured. Log file: {log_filename}")
    return logger