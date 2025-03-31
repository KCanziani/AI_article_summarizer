"""
Web scraping functionality for AI News Scraper
Contains functions to scrape articles from various news sources
"""

import logging
from datetime import datetime, timedelta
from .summarizer import summarize_with_openai
from config.config import AI_NEWS_URL, MIT_NEWS_URL, STANFORD_NEWS_URL, YOUTUBE_API_KEY, YOUTUBE_CHANNELS
from .email_sender import send_combined_email_report
from .scraper import scrape_articles_AI_news, get_article_content, scrape_mit_articles, get_mit_article_content, scrape_stanford_articles, get_stanford_article_content
from .youtube_scraper import process_youtube_channels
import csv

# Get logger
logger = logging.getLogger('ai_news_scraper.processor')

def save_to_csv(articles, filename) -> None:
    """
    Save articles to CSV file.
    
    Args:
        articles (List[Dict]): List of articles to save
        filename (str): Path to save the CSV file
    """
    try:
        keys = ['Title', 'Date', 'Link','Summary', 'Source']
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=keys, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(articles)
        logger.info(f"Articles saved to CSV: {filename}")
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
            
        logger.info(f"Articles saved to HTML: {filename}")
        
    except Exception as e:
        logger.error(f"Error saving to HTML: {e}")
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

        logger.info(f"Processing news for date range: {date_str}")

        # Get and process articles
        all_articles = []
        source_counts = {}  # Para llevar la cuenta de artículos por fuente

        source_configs = [
            ('AI News', scrape_articles_AI_news, get_article_content),
            ('MIT News', scrape_mit_articles, get_mit_article_content),
            ('Stanford News', scrape_stanford_articles, get_stanford_article_content)
        ]

        # Collect articles from all sources
        for source_name, scraper_func, content_func in source_configs:
            try:
                logger.info(f"Processing source: {source_name}")
                url = globals()[f"{source_name.upper().replace(' ', '_')}_URL"]
                articles = scraper_func(url)
                
                source_articles = []  # Artículos para esta fuente

                # Process each article
                for article in articles:
                    article_date = article.get('Date')
                    
                    # Check if article is within date range
                    if article_date and start_date <= article_date <= end_date:
                        # Get and summarize content
                        content = content_func(article['Link'])
                        if content:
                            article['Summary'] = "not summary yet" #summarize_with_openai(content)
                        article['Source'] = source_name
                        all_articles.append(article)
                        source_articles.append(article)

                source_counts[source_name] = len(source_articles)
                logger.info(f"Found {len(source_articles)} articles from {source_name}")
        
            except Exception as e:
                logger.error(f"Error processing {source_name}: {e}")
                source_counts[source_name] = 0
                continue

        # Process YouTube channels
        try:
            if YOUTUBE_API_KEY and YOUTUBE_CHANNELS:
                youtube_articles = process_youtube_channels(
                    YOUTUBE_API_KEY, 
                    YOUTUBE_CHANNELS,
                    max_videos=10
                )
                
                all_articles = all_articles.extend(youtube_articles)
                source_counts['YouTube'] = len(youtube_articles)
                logger.info(f"Added {len(youtube_articles)} YouTube videos to articles")
            else:
                logger.info("YouTube processing skipped: API key or channels not configured")
                source_counts['YouTube'] = 0
            
        except Exception as e:
            logger.error(f"Error processing YouTube channels: {e}")
            source_counts['YouTube'] = 0

        # Log total counts
        logger.info(f"Total articles collected: {len(all_articles)}")
        for source, count in source_counts.items():
            logger.info(f"  - {source}: {count} articles")
        

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
            logger.info("Articles processed, saved, and email sent successfully!")
        else:
            logger.info(f"No articles found for date range: {date_str}")
    
    except Exception as e:
        logger.error(f"Error in process_all_news: {e}")
        raise