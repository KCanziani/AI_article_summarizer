#!/usr/bin/env python3
from dotenv import load_dotenv
import os
import logging
import json 
from src.scraper import process_all_news

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


def main():
    """
    Main function to orchestrate the AI News Summary email process.
    """
    # Setup logging
    logging.basicConfig(
        format='%(asctime)s %(levelname)s: %(message)s',
        level=logging.INFO
    )

    try:
        # Fetch and process articles
        logging.info("Fetching and processing articles...")
        process_all_news(RECIPIENT_EMAIL)

    except Exception as e:
        logging.error(f"An error occurred in the main process: {e}")
        raise

if __name__ == "__main__":
    main()
