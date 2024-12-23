# Article Scraper and Summarizer

## Overview
This project scrapes articles from a news website, summarizes them using OpenAI, and outputs the results in CSV and HTML formats. It automates content extraction and provides concise summaries for easy review. This tool is particularly useful for staying up-to-date with AI-related news, offering a quick way to skim summaries and open articles of interest.

## Features
- Scrapes articles from [Artificial Intelligence News](https://www.artificialintelligence-news.com).
- Summarizes articles using OpenAI's GPT model.
- Outputs results as a CSV file and a styled HTML file.

## Files
- `script.ipynb`: Jupyter Notebook containing the main code.
- `data/articles_<date>.csv`: CSV file with scraped and summarized articles.
- `results/output.html`: HTML file with clickable links and summaries.

## How to Run
1. Clone the repository.
2. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `config.py` file in the root folder of the repository and save your OpenAI API key with the variable name:
   ```python
   OPENAI_API_KEY = "your_openai_api_key"
   ```
4. Open `AI_news_summary_web.ipynb` in Jupyter Notebook or VSCode and run the cells.
5. Find the generated files in the `data/` and `results/` folders.

## Why It’s Useful
- Quickly review the latest news without having to visit multiple websites.
- Access concise summaries to decide which articles are worth reading in full.
- Clickable links make it easy to open the original articles.

## Preview
![HTML Output Example](results/output_example.png)
