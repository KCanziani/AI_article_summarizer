"""
Initialize the src package
Contains version information and package-level imports
"""

__version__ = '1.1.0'

from .scraper import (
    scrape_articles_AI_news, 
    get_article_content, 
    scrape_mit_articles, 
    get_mit_article_content, 
    scrape_stanford_articles, 
    get_stanford_article_content
)
from .summarizer import summarize_with_openai
from .email_sender import send_combined_email_report
from .utils import parse_article_date, safe_str, setup_http_session
from .youtube_scraper import (
    build_youtube_client,
    get_channel_id,
    get_recent_videos,
    download_subtitles,
    get_video_transcript,
    process_youtube_channels
)

__all__ = [
    'send_combined_email_report',
    'summarize_with_openai',
    'parse_article_date',
    'safe_str',
    'setup_http_session',
    
    # Web scrapers
    'scrape_articles_AI_news',
    'get_article_content',
    'scrape_mit_articles',
    'get_mit_article_content',
    'scrape_stanford_articles',
    'get_stanford_article_content',
    
    # YouTube scraper
    'build_youtube_client',
    'get_channel_id',
    'get_recent_videos',
    'download_subtitles',
    'get_video_transcript',
    'process_youtube_channels'
]