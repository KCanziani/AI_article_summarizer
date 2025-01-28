# email_sender.py

"""
Email functionality for sending news summaries
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Union
from config.config import EMAIL, PASSWORD
from .utils import safe_str

def send_combined_email_report(articles: List[Dict], date_str: str, recipients: Union[str, List[str]]) -> None:
    """
    Sends email report with summarized articles.
    """
    try:
        if not recipients:
            raise ValueError("No recipients provided")

        html_content = _create_email_html(articles, date_str)
        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(EMAIL, PASSWORD)
            
            # Handle different recipient formats
            if isinstance(recipients, str):
                if recipients.startswith('[') and recipients.endswith(']'):
                    try:
                        recipient_list = json.loads(recipients)
                    except json.JSONDecodeError:
                        recipient_list = [recipients]
                else:
                    recipient_list = [recipients]
            else:
                recipient_list = recipients

            # Validate recipient list
            if not recipient_list:
                raise ValueError("No valid recipients found")
            
            for recipient in recipient_list:
                if not isinstance(recipient, str) or not recipient.strip():
                    logging.warning(f"Skipping invalid recipient: {recipient}")
                    continue
                    
                try:
                    msg = _create_email_message(recipient.strip(), date_str, html_content)
                    server.send_message(msg)
                    logging.info(f"Email sent successfully to {recipient}")
                except Exception as e:
                    logging.error(f"Error sending email to {recipient}: {e}")
                    
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error: {e}")
        raise
    except Exception as e:
        logging.error(f"Error in email sending process: {e}")
        raise

def _create_email_html(articles: List[Dict], date_str: str) -> str:
    """
    Creates HTML content for email.
    
    Args:
        articles (List[Dict]): List of processed articles
        date_str (str): Date range string for the report
        
    Returns:
        str: Formatted HTML content
    """
    css_styles = """
        table { 
            border-collapse: collapse; 
            width: 100%; 
            margin-bottom: 30px;
            font-family: Arial, sans-serif;
        }
        th, td { 
            padding: 12px; 
            text-align: left; 
            border: 1px solid #ddd; 
        }
        th { 
            background-color: #914048; 
            color: white; 
            font-weight: bold;
        }
        tr:nth-child(even) {
            background-color: #f9f9f9;
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .source-header {
            background-color: #f5f5f5;
            padding: 15px;
            margin: 25px 0 15px 0;
            font-size: 1.2em;
            font-weight: bold;
            border-left: 4px solid #914048;
        }
        a {
            color: #914048;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
    """
    
    html_template = f"""
    <html>
        <head>
            <meta charset="UTF-8">
            <style>{css_styles}</style>
        </head>
        <body>
            <h2>Weekly AI News Summary - {date_str}</h2>
    """
    
    # Add content for each source
    sources = ['AI News', 'MIT News', 'Stanford News']
    for source in sources:
        source_articles = [a for a in articles if a.get('Source') == source]
        if source_articles:
            html_template += _create_source_section(source, source_articles)
    
    html_template += """
        </body>
    </html>
    """
    return html_template

def _create_source_section(source: str, articles: List[Dict]) -> str:
    """
    Creates HTML section for a specific news source.
    
    Args:
        source (str): Name of the news source
        articles (List[Dict]): List of articles for this source
        
    Returns:
        str: HTML content for the source section
    """
    html = f'<div class="source-header">{source}</div>'
    html += """
    <table>
        <tr>
            <th>Title</th>
            <th>Date</th>
            <th>Summary</th>
        </tr>
    """
    
    for article in articles:
        title = safe_str(article.get('Title', ''))
        link = safe_str(article.get('Link', ''))
        date = safe_str(article.get('Date', ''))
        summary = safe_str(article.get('Summary', ''))
        
        html += f"""
        <tr>
            <td><a href="{link}" target="_blank">{title}</a></td>
            <td>{date}</td>
            <td>{summary}</td>
        </tr>
        """
    
    html += "</table>"
    return html

def _create_email_message(recipient: str, date_str: str, html_content: str) -> MIMEMultipart:
    """
    Creates email message with proper headers.
    
    Args:
        recipient (str): Email recipient
        date_str (str): Date range string for the subject
        html_content (str): HTML content of the email
        
    Returns:
        MIMEMultipart: Formatted email message
    """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'Weekly AI News Summary - {date_str}'
    msg['From'] = EMAIL
    msg['To'] = recipient
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    return msg