"""
Main entry point for AI News Scraper
"""

#!/usr/bin/env python3
from dotenv import load_dotenv
import os
import sys
import json 
from src.process_all_news import process_all_news
from src.utils import setup_logging

# Load environment variables from the .env file
load_dotenv()

# Retrieve environment variables
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")
RECIPIENT_EMAIL = json.loads(os.getenv("RECIPIENT_EMAILS", "[]"))
if not RECIPIENT_EMAIL:
    raise ValueError("No recipient emails configured")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def main():
    """Main function to run the AI News Scraper"""
    # Setup logging
    logger = setup_logging()
    
    try:
        logger.info("Starting AI News Scraper")
        
        # Check for command line args (target date)
        target_date = '2025-03-16'
        if len(sys.argv) > 1:
            target_date = sys.argv[1]
            logger.info(f"Target date provided: {target_date}")
            
        # Process news
        process_all_news(RECIPIENT_EMAIL, target_date)
        
        logger.info("AI News Scraper completed successfully")
        return 0
        
    except Exception as e:
        logger.critical(f"Critical error in main function: {e}")
        logger.exception("Exception details:")
        return 1

if __name__ == "__main__":
    sys.exit(main())