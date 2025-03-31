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

def send_combined_email_report(articles: List[Dict], date_str: str, recipients: Union[str, List[str]]) -> None:
    """
    Sends email report with summarized articles.
    """
    try:
        if not recipients:
            raise ValueError("No recipients provided")

        # Generate HTML content 
        html_content = generate_email_html(articles, date_str)
        
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

def generate_email_html(articles, date_str):
    """
    Generate HTML content for email from articles.
    
    Args:
        articles (list): List of processed articles
        date_str (str): Date range string for the title
        
    Returns:
        str: HTML content for the email
    """
    try:
        import pandas as pd
        
        if not articles:
            logging.warning("No articles to include in the email")
            return "<p>No articles found for this period.</p>"

        # Define function to make links clickable
        def make_clickable(val):
            return f'<a href="{val}" target="_blank">{val}</a>'

        # Define CSS styles - modified for email compatibility
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
            # Row hover style
            dict(selector="tr:hover", props=[
                ("background-color", "#f5f5f5")
            ]),
            # Even rows
            dict(selector="tr:nth-child(even)", props=[
                ("background-color", "#f9f9f9")
            ])
        ]

        # Create HTML template
        html_template = f"""
        <html>
        <head>
            <meta charset="UTF-8">
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
                a {{
                    color: #914048;
                    text-decoration: none;
                }}
                a:hover {{
                    text-decoration: underline;
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
                
                # Select and reorder columns for email
                # Note: Changed to include only the columns you want in the email
                columns_to_display = ['Title', 'Date', 'Summary']
                df_display = df_source[columns_to_display].copy()
                
                # Format the date column
                df_display['Date'] = df_display['Date'].apply(lambda x: x.strftime('%Y-%m-%d') if pd.notnull(x) else '')
                
                # Add the link to the title instead of showing it separately
                if 'Link' in df_source.columns:
                    # Create a new Title column with embedded links
                    df_display['Title'] = df_source.apply(
                        lambda row: f'<a href="{row["Link"]}" target="_blank">{row["Title"]}</a>',
                        axis=1
                    )
                
                # Style the DataFrame
                df_styled = df_display.style.set_table_styles(styles)
                
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

        return html_template
            
    except Exception as e:
        logging.error(f"Error generating email HTML: {e}")
        # Return a simple error message if something goes wrong
        return f"<p>Error generating email content: {str(e)}</p>"

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