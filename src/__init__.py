"""
Initialize the src package
Contains version information and package-level imports
"""

__version__ = '1.0.0'

from .scraper import process_all_news
from .summarizer import summarize_with_openai
from .email_sender import send_combined_email_report
from .utils import parse_article_date, safe_str, setup_http_session

__all__ = [
    'process_all_news',
    'summarize_with_openai',
    'send_combined_email_report',
    'parse_article_date',
    'safe_str',
    'setup_http_session'
]