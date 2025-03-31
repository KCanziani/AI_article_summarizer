"""
Web scraping functionality for AI News Scraper
Contains functions to scrape articles from various news sources
"""

import logging
from datetime import datetime
from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException
from .utils import parse_article_date, setup_http_session

# Initialize HTTP session
session = setup_http_session()

def scrape_articles_AI_news(url):
    """
    Scrapes articles from the provided website URL.
    
    Args:
        url (str): URL of the website to scrape articles from.
    
    Returns:
        list: A list of dictionaries, where each dictionary contains article data (title, link, date).
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        response = session.get(url, timeout=30, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        article_data = []

        # Find the Featured section
        featured_section = soup.find('section', class_='featured')
        if featured_section:

            # Find all featured article blocks with specific class
            featured_blocks = featured_section.find_all('div', class_='cell blocks small-12 medium-3 large-3')

            for block in featured_blocks:
                try:
                    # Get the image link and title
                    link_element = block.find('a', class_='img-link')
                    title_element = block.find('h3')
                    date_div = block.find('div', class_='content')  # Date extraction

                    if link_element and title_element:
                        title = link_element['title'].strip()  # Title is in the link's title attribute
                        link = link_element['href'].strip()   # Article URL
                        date_str = date_div.text.strip().split('|')[0].strip() if date_div else 'No date available'
                        date = parse_article_date(date_str) 

                        article_data.append({
                            'Title': title,
                            'Link': link,
                            'Date': date,
                            'Source': "AI News"
                        })

                except Exception as e:
                    logging.warning(f"Error processing featured article: {e}")
                    continue

        # Get regular articles
        regular_articles = soup.find_all('article')

        for article in regular_articles:
            try:
                title = article.find('h3').get_text(strip=True)
                link = article.find('a')['href']
                date_div = article.find('div', class_='content')
                date_str = date_div.text.strip().split('|')[0].strip() if date_div else 'No date available'
                date = parse_article_date(date_str)

                # Check if this article is already in our list
                if not any(a['Link'] == link for a in article_data):
                    article_data.append({
                        'Title': title,
                        'Link': link,
                        'Date': date,
                        'Source': "AI News"
                    })
            except Exception as e:
                logging.warning(f"Error processing article: {e}")
                continue

        return article_data
    except RequestException as e:
        logging.error(f"Request error: {e}")
        return []


# Function to fetch the content of an article
def get_article_content(url):
    """
    Fetches the main content of an article from its URL.

    Args:
        url (str): URL of the article.

    Returns:
        str: Extracted article content or None if extraction fails.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = session.get(url, timeout=30, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        content_container = soup.find('div', class_='article-content') or soup.find('article')

        if content_container:
            paragraphs = content_container.find_all('p')
            return ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        return ""
    except RequestException as e:
        logging.error(f"Error fetching article content: {e}")
        return ""
    
def scrape_mit_articles(url):
    """
    Scrapes articles from MIT AI News
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        article_data = []

        # Find all article elements with the correct class
        articles = soup.find_all('article', class_='term-page--news-article--item')

        for article in articles:
            try:
                # Extract title
                title_element = article.find('h3', class_='term-page--news-article--item--title')
                title = title_element.find('a').get_text(strip=True) if title_element else None

                # Extract link
                link_element = article.find('a', class_='term-page--news-article--item--title--link')
                link = link_element['href'] if link_element else None
                if link and not link.startswith('http'):
                    link = f"https://news.mit.edu{link}"

                # Extract date and convert to date object
                date_element = article.find('time')
                date_str = date_element['datetime'] if date_element else None
                if date_str:
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00')).date()
                else:
                    date_obj = None

                # # Extract summary
                # summary_element = article.find('p', class_='term-page--news-article--item--dek')
                # summary = summary_element.get_text(strip=True) if summary_element else None

                if all([title, link]):  # Add article if at least title and link are present
                    article_data.append({
                        'Title': title,
                        'Link': link,
                        'Date': date_obj,
                        'Source': "MIT News"
                    })

            except Exception as e:
                logging.warning(f"Error processing MIT article: {e}")
                continue

        return article_data
    except Exception as e:
        logging.error(f"Error in scraping MIT: {e}")
        return []

def get_mit_article_content(url):
    """
    Fetches the content of a MIT News article
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to find the main article content
        content_container = (
            soup.find('div', class_='news-article--content--body') or  # Try specific content class first
            soup.find('article') or                                    # Then try main article tag
            soup.find('main')                                         # Finally try main content area
        )
        
        if content_container:
            # Get all paragraphs
            paragraphs = content_container.find_all('p')
            
            # Clean and join the text
            content = ' '.join([
                p.get_text(strip=True) 
                for p in paragraphs 
                if p.get_text(strip=True) and 
                   'Previous image' not in p.get_text() and
                   'Next image' not in p.get_text()
            ])
            
            # Additional cleaning
            content = content.replace('Previous imageNext image', '')
            
            if len(content) > 100:  # Basic check to ensure we got meaningful content
                return content
                
        return ""
    except Exception as e:
        logging.err

def scrape_stanford_articles(url):
    """
    Scrapes articles from Stanford AI News
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        }
        
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        article_data = []

        news_container = soup.find('div', {'data-component': 'topic-subtopic-listing'})
        if news_container:
            import json
            props = json.loads(news_container['data-hydration-props'])
            articles = props.get('data', [])
            
            for article in articles:
                try:
                    # Convert timestamp to date object immediately
                    if article.get('date'):
                        date_obj = datetime.fromtimestamp(article.get('date')/1000).date()
                    else:
                        date_obj = None

                    #summary = article.get('description', [''])[0] if isinstance(article.get('description'), list) else article.get('description')
                    article_data.append({
                        'Title': article.get('title'),
                        'Link': article.get('liveUrl'),
                        'Date': date_obj,
                        'Source': "Stanford News"
                    })

                except Exception as e:
                    logging.warning(f"Error processing Stanford article: {e}")
                    continue

        return article_data
    
    except Exception as e:
        logging.error(f"Error in scraping Stanford: {e}")
        return []
        
def get_stanford_article_content(url):
    """
    Fetches the content of a Stanford News article
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, timeout=30, headers=headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        # Find the main article content
        content_container = soup.find('div', class_='su-page-content') or soup.find('article')
        
        if content_container:
            paragraphs = content_container.find_all('p')
            return ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        return ""
    except Exception as e:
        logging.error(f"Error fetching Stanford article content: {e}")
        return ""



