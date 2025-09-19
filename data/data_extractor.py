import json
import requests
from bs4 import BeautifulSoup
import time
import csv
from urllib.parse import urljoin
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ArticleScraper:
    def __init__(self, json_file_path, output_file='scraped_articles.csv', delay=1):
        """
        Initialize the scraper
        
        Args:
            json_file_path (str): Path to the JSON file containing article metadata
            output_file (str): Path for the output CSV file
            delay (int): Delay between requests in seconds
        """
        self.json_file_path = json_file_path
        self.output_file = output_file
        self.delay = delay
        self.session = requests.Session()
        # Set a user agent to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def load_json_data(self):
        """Load and parse the JSON file"""
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            logger.info(f"Loaded {len(data)} articles from JSON file")
            return data
        except FileNotFoundError:
            logger.error(f"JSON file not found: {self.json_file_path}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON file: {e}")
            return None
    
    def extract_pmc_content(self, url):
        """
        Extract content from PMC articles
        
        Args:
            url (str): URL of the PMC article
            
        Returns:
            str: Extracted article content
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # PMC articles typically have content in these sections
            content_selectors = [
                '.article-text',
                '.article-body',
                '#article-body',
                '.content',
                'div[data-section-title]',
                '.sec'
            ]
            
            content_parts = []
            
            # Try different selectors for PMC content
            for selector in content_selectors:
                elements = soup.select(selector)
                for element in elements:
                    # Remove script and style elements
                    for script in element(["script", "style"]):
                        script.decompose()
                    text = element.get_text(strip=True)
                    if text and len(text) > 100:  # Only add substantial content
                        content_parts.append(text)
            
            # If no content found with selectors, try getting main content area
            if not content_parts:
                # Look for the main article content div
                main_content = soup.find('div', {'class': 'article'}) or soup.find('main') or soup.find('article')
                if main_content:
                    # Remove unwanted elements
                    for unwanted in main_content(["script", "style", "nav", "header", "footer", ".sidebar"]):
                        unwanted.decompose()
                    text = main_content.get_text(strip=True)
                    if text:
                        content_parts.append(text)
            
            # Join all content parts
            full_content = ' '.join(content_parts)
            
            # Clean up the text
            full_content = ' '.join(full_content.split())  # Remove extra whitespace
            
            return full_content[:5000] if len(full_content) > 5000 else full_content  # Limit length
            
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return f"Error fetching content: {str(e)}"
        except Exception as e:
            logger.error(f"Error processing {url}: {e}")
            return f"Error processing content: {str(e)}"
    
    def extract_authors(self, authors_list):
        """
        Extract author names from the authors list
        
        Args:
            authors_list (list): List of author names
            
        Returns:
            str: Comma-separated author names
        """
        if isinstance(authors_list, list) and authors_list:
            return ', '.join(authors_list)
        return "No authors listed"
    
    def scrape_articles(self):
        """Main method to scrape all articles"""
        # Load JSON data
        articles_data = self.load_json_data()
        if not articles_data:
            return
        
        # Prepare output data
        scraped_data = []
        
        # Process each article
        for i, article in enumerate(articles_data, 1):
            logger.info(f"Processing article {i}/{len(articles_data)}")
            
            # Extract basic metadata
            pmid = article.get('pmid', 'N/A')
            title = article.get('title', 'N/A')
            authors = self.extract_authors(article.get('authors', []))
            
            # Get the full text URL
            full_text_links = article.get('full_text_links', [])
            content = "No content available"
            url = "No URL available"
            
            if full_text_links and isinstance(full_text_links, list):
                for link in full_text_links:
                    if isinstance(link, dict) and 'url' in link:
                        url = link['url']
                        if 'pmc.ncbi.nlm.nih.gov' in url or 'pubmed' in url:
                            logger.info(f"Scraping content from: {url}")
                            content = self.extract_pmc_content(url)
                            break
            
            # Create article record
            article_record = {
                'pmid': pmid,
                'title': title,
                'authors': authors,
                'url': url,
                'content': content
            }
            
            scraped_data.append(article_record)
            
            # Add delay between requests
            if i < len(articles_data):
                time.sleep(self.delay)
        
        # Save to CSV
        self.save_to_csv(scraped_data)
        logger.info(f"Scraping completed! Data saved to {self.output_file}")
        
        return scraped_data
    
    def save_to_csv(self, data):
        """Save scraped data to CSV file"""
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['pmid', 'title', 'authors', 'url', 'content']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
                    
            logger.info(f"Data successfully saved to {self.output_file}")
        except Exception as e:
            logger.error(f"Error saving to CSV: {e}")
    
    def save_to_json(self, data, json_output_file='scraped_articles.json'):
        """Save scraped data to JSON file"""
        try:
            with open(json_output_file, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=2, ensure_ascii=False)
            logger.info(f"Data successfully saved to {json_output_file}")
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")

# Usage example
if __name__ == "__main__":
    # Initialize the scraper
    scraper = ArticleScraper(
        json_file_path='muscle_hypertrophy_articles.json',  
        output_file='scraped_articles.csv',
        delay=2  # 2 seconds delay between requests to be respectful to servers
    )
    
    # Start scraping
    scraped_data = scraper.scrape_articles()
    
    # Optionally save to JSON as well
    scraper.save_to_json(scraped_data)
    
    # Print summary
    if scraped_data:
        print(f"\nScraping Summary:")
        print(f"Total articles processed: {len(scraped_data)}")
        successful_scrapes = sum(1 for article in scraped_data if not article['content'].startswith('Error') and article['content'] != "No content available")
        print(f"Successfully scraped: {successful_scrapes}")
        print(f"Failed/No content: {len(scraped_data) - successful_scrapes}")