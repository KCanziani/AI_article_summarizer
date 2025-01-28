"""
Web scraping functionality for AI News Scraper
Contains functions to scrape articles from various news sources
"""

import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import requests
from requests.exceptions import RequestException
import json
import csv
import pandas as pd
from datetime import datetime, timedelta
from .utils import parse_article_date, setup_http_session
from .summarizer import summarize_with_openai
from config.config import AI_NEWS_URL, MIT_NEWS_URL, STANFORD_NEWS_URL
from .email_sender import send_combined_email_report
from typing import List, Dict, Optional

# Initialize HTTP session
session = setup_http_session()

def scrape_articles(url):
    """
    Scrapes articles from the provided website URL.
    
    Args:
        url (str): URL of the website to scrape articles from.
    
    Returns:
        list: A list of dictionaries, where each dictionary contains article data (title, link, date, type).
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
                            'Type': 'featured'
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
                        'Type': 'regular'
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

                # Extract summary
                summary_element = article.find('p', class_='term-page--news-article--item--dek')
                summary = summary_element.get_text(strip=True) if summary_element else None

                if all([title, link]):  # Add article if at least title and link are present
                    article_data.append({
                        'Title': title,
                        'Link': link,
                        'Date': date_obj,
                        'Summary': summary
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

                    article_data.append({
                        'Title': article.get('title'),
                        'Link': article.get('liveUrl'),
                        'Date': date_obj,
                        'Summary': article.get('description', [''])[0] if isinstance(article.get('description'), list) else article.get('description')
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



def save_to_csv(articles: List[Dict], filename: str) -> None:
    """
    Save articles to CSV file.
    
    Args:
        articles (List[Dict]): List of articles to save
        filename (str): Path to save the CSV file
    """
    try:
        keys = ['Title', 'Date', 'Link', 'Type', 'Summary', 'Source']
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(articles)
        logging.info(f"Articles saved to {filename}")
    except Exception as e:
        logging.error(f"Error saving to CSV: {e}")
        raise

def save_to_html(articles, date_str, filename):
    """
    Save articles to a styled HTML file.
    
    Args:
        articles (list): List of processed articles
        date_str (str): Date range string for the title
        filename (str): Path to save the HTML file
    """
    try:
        import pandas as pd
        
        if not articles:
            logging.warning("No articles to save to HTML")
            return

        # Convert to DataFrame
        df = pd.DataFrame(articles)
        
        # Define function to make links clickable
        def make_clickable(val):
            return f'<a href="{val}" target="_blank">{val}</a>'

        # Define CSS styles
        styles = [
            # Header style
            dict(selector="th", props=[
                ("background-color", "#914048"),
                ("color", "white"),
                ("font-weight", "bold"),
                ("text-align", "center"),
                ("padding", "10px"),
                ("border", "1px solid #ddd")
            ]),
            # Cell style
            dict(selector="td", props=[
                ("border", "1px solid #ddd"),
                ("padding", "8px"),
                ("text-align", "left")
            ]),
            # Table style
            dict(selector="", props=[
                ("border-collapse", "collapse"),
                ("width", "100%"),
                ("margin", "20px 0"),
                ("font-family", "Arial, sans-serif")
            ]),
            # Source group style
            dict(selector=".source-header", props=[
                ("background-color", "#f5f5f5"),
                ("padding", "10px"),
                ("margin", "20px 0 10px 0"),
                ("font-size", "1.2em"),
                ("font-weight", "bold")
            ])
        ]

        # Create HTML template
        html_template = f"""
        <html>
        <head>
            <title>AI News Summary - {date_str}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 20px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                h1 {{
                    color: #333;
                    text-align: center;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #914048;
                }}
                .source-section {{
                    margin-top: 30px;
                }}
                .source-header {{
                    background-color: #f5f5f5;
                    padding: 10px;
                    margin: 20px 0 10px 0;
                    font-size: 1.2em;
                    font-weight: bold;
                    border-left: 4px solid #914048;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>AI News Summary - {date_str}</h1>
        """

        # Group articles by source
        sources = sorted(set(article['Source'] for article in articles))
        
        for source in sources:
            source_articles = [a for a in articles if a['Source'] == source]
            if source_articles:
                # Create DataFrame for this source
                df_source = pd.DataFrame(source_articles)
                
                # Select and reorder columns
                columns_to_display = ['Title', 'Date', 'Link', 'Summary']
                df_display = df_source[columns_to_display].copy()
                
                # Format the date column
                df_display['Date'] = df_display['Date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '')
                
                # Style the DataFrame
                df_styled = df_display.style\
                    .format({'Link': make_clickable})\
                    .set_table_styles(styles)
                
                # Add source section to HTML
                html_template += f"""
                    <div class="source-section">
                        <div class="source-header">{source}</div>
                        {df_styled.to_html(escape=False)}
                    </div>
                """

        html_template += """
            </div>
        </body>
        </html>
        """

        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_template)
            
        logging.info(f"HTML report saved to {filename}")
        
    except Exception as e:
        logging.error(f"Error saving to HTML: {e}")
        raise

def process_all_news(recipients, target_date=None):
    """
    Process news from all sources and send combined email.
    
    Args:
        recipients (str or list): Email recipient(s)
        target_date (str, optional): Target date in YYYY-MM-DD format
        
    Returns:
        None
    """
    try:
        # Set date range
        end_date = (datetime.strptime(target_date, '%Y-%m-%d').date() 
                   if target_date else datetime.now().date())
        start_date = end_date - timedelta(days=7)
        date_str = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

        logging.info(f"Processing news for date range: {date_str}")

        # Get and process articles
        all_articles = []
        source_configs = [
            ('AI News', scrape_articles, get_article_content),
            ('MIT News', scrape_mit_articles, get_mit_article_content),
            ('Stanford News', scrape_stanford_articles, get_stanford_article_content)
        ]

        # Collect articles from all sources
        for source_name, scraper_func, content_func in source_configs:
            try:
                url = globals()[f"{source_name.upper().replace(' ', '_')}_URL"]
                articles = scraper_func(url)
                
                # Process each article
                for article in articles:
                    article_date = article.get('Date')
                    
                    # Check if article is within date range
                    if article_date and start_date <= article_date <= end_date:
                        # Get and summarize content
                        content = content_func(article['Link'])
                        if content:
                            article['Summary'] = "Summary not available" #summarize_with_openai(content)
                        article['Source'] = source_name
                        all_articles.append(article)
                        
            except Exception as e:
                logging.error(f"Error processing {source_name}: {e}")
                continue

        if all_articles:
            # Create date string for filenames
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            # Save to CSV
            csv_path = f"data/articles_week_{end_date_str}.csv"
            save_to_csv(all_articles, csv_path)
            
            # Save to HTML
            html_path = f"results/articles_week_{end_date_str}.html"
            save_to_html(all_articles, date_str, html_path)
            
            # Send email
            send_combined_email_report(all_articles, date_str, recipients)
            logging.info("Articles processed, saved, and email sent successfully!")
        else:
            logging.info(f"No articles found for date range: {date_str}")

    except Exception as e:
        logging.error(f"Error in process_all_news: {e}")
        raise