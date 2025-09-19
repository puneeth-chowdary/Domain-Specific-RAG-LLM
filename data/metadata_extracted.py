import requests
from bs4 import BeautifulSoup
import time
import csv
import json
from urllib.parse import urljoin
import re

class PubMedScraper:
    def __init__(self, delay=2):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.delay = delay
        self.scraped_data = []
        self.base_url = "https://pubmed.ncbi.nlm.nih.gov"
    
    def get_page(self, url):
        """Fetch a webpage with error handling"""
        try:
            print(f"Fetching: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            time.sleep(self.delay)
            return response
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_pmids_from_search(self, search_url, pages=3):
        """Extract PMIDs from PubMed search results across multiple pages"""
        all_pmids = []
        
        for page_num in range(1, pages + 1):
            # Create the paginated URL
            if '&page=' in search_url:
                page_url = re.sub(r'&page=\d+', f'&page={page_num}', search_url)
            else:
                page_url = f"{search_url}&page={page_num}"
                
            print(f"Extracting PMIDs from page {page_num}: {page_url}")
            response = self.get_page(page_url)
            if not response:
                print(f"Failed to fetch page {page_num}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')
            pmids = []

            # PubMed search results links like "/35389932/"
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href and re.match(r'^/\d+/?$', href):
                    pmid = href.strip('/')
                    if pmid.isdigit():
                        pmids.append(pmid)

            # Remove duplicates while preserving order
            seen = set()
            ordered_pmids = []
            for pmid in pmids:
                if pmid not in seen:
                    seen.add(pmid)
                    ordered_pmids.append(pmid)

            print(f"Found {len(ordered_pmids)} PMIDs on page {page_num}")
            all_pmids.extend(ordered_pmids)
            
            # Check if we've reached the end of results
            next_button = soup.find('button', class_='next-page-btn')
            if not next_button or 'disabled' in next_button.get('class', []):
                print("No more pages available")
                break

        # Limit to 600 articles (200 per page for 3 pages)
        all_pmids = all_pmids[:600]
        print(f"Total unique PMIDs found: {len(all_pmids)}")
        return all_pmids

    def get_article_details(self, pmid):
        """Get article details from PubMed"""
        article_url = f"{self.base_url}/{pmid}/"
        response = self.get_page(article_url)
        if not response:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')
        article_data = {
            'pmid': pmid,
            'url': article_url,
            'title': '',
            'authors': [],
            'journal': '',
            'publication_date': '',
            'abstract': '',
            'doi': '',
            'full_text_links': [],
            'full_text_content': ''
        }

        # Title
        title_elem = soup.find('h1', class_='heading-title')
        if title_elem:
            article_data['title'] = title_elem.get_text(strip=True)

        # Authors
        author_list = soup.find('div', class_='authors-list')
        if author_list:
            authors = author_list.find_all('a', class_='full-name')
            article_data['authors'] = [a.get_text(strip=True) for a in authors]

        # Journal
        journal_elem = soup.find('button', class_='journal-actions-trigger')
        if journal_elem:
            article_data['journal'] = journal_elem.get_text(strip=True)

        # Publication date
        date_elem = soup.find('span', class_='cit')
        if date_elem:
            article_data['publication_date'] = date_elem.get_text(strip=True)

        # Abstract
        abstract_elem = soup.find('div', class_='abstract-content')
        if abstract_elem:
            article_data['abstract'] = abstract_elem.get_text(strip=True)

        # DOI
        doi_elem = soup.find('span', class_='citation-doi')
        if doi_elem:
            doi_link = doi_elem.find('a')
            if doi_link:
                article_data['doi'] = doi_link.get_text(strip=True)

        return article_data

    def find_full_text_links(self, pmid, article_data):
        """Find full text links for an article"""
        print(f"Looking for full text links for PMID: {pmid}")
        response = self.get_page(article_data['url'])
        if not response:
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        full_text_links = []

        # Full Text Links section
        full_text_section = soup.find('div', class_='full-text-links-list')
        if full_text_section:
            for link in full_text_section.find_all('a', href=True):
                href = link['href']
                text = link.get_text(strip=True)
                if href.startswith('/'):
                    href = urljoin('https://www.ncbi.nlm.nih.gov', href)
                full_text_links.append({
                    'url': href,
                    'source': text,
                    'type': self.categorize_link_type(href, text)
                })

        # PMC free full text
        pmc_link = soup.find('a', href=re.compile(r'/pmc/articles/'))
        if pmc_link:
            pmc_url = urljoin('https://www.ncbi.nlm.nih.gov', pmc_link['href'])
            full_text_links.append({
                'url': pmc_url,
                'source': 'PMC Free Full Text',
                'type': 'pmc'
            })

        article_data['full_text_links'] = full_text_links
        print(f"Found {len(full_text_links)} full text links for PMID {pmid}")
        return full_text_links

    def categorize_link_type(self, url, link_text):
        url_lower = url.lower()
        text_lower = link_text.lower()
        if 'pmc' in url_lower:
            return 'pmc'
        elif 'pdf' in url_lower or 'pdf' in text_lower:
            return 'pdf'
        elif any(publisher in url_lower for publisher in ['pubmed', 'ncbi']):
            return 'ncbi'
        elif any(publisher in url_lower for publisher in ['springer', 'elsevier', 'wiley', 'nature', 'science']):
            return 'publisher'
        else:
            return 'external'

    def scrape_pmc_full_text(self, pmc_url):
        """Scrape full text from PMC"""
        print(f"Scraping PMC full text: {pmc_url}")
        response = self.get_page(pmc_url)
        if not response:
            return ""

        soup = BeautifulSoup(response.content, 'html.parser')
        content_sections = []

        # Abstract
        abstract = soup.find('div', class_='abstract')
        if abstract:
            content_sections.append("ABSTRACT:\n" + abstract.get_text(strip=True))

        # Main content
        article_content = soup.find('div', class_='PMC-article-content') or soup.find('div', class_='article-body')
        if article_content:
            for elem in article_content.find_all(['div', 'span'], class_=re.compile(r'(ref|fig|table)')):
                elem.decompose()
            for section in article_content.find_all(['div', 'section'], class_=re.compile(r'sec')):
                text = section.get_text(strip=True)
                if len(text) > 50:
                    content_sections.append(text)

        return "\n\n".join(content_sections)

    def get_full_text_content(self, article_data):
        """Get full text content from available links"""
        links = article_data.get('full_text_links', [])
        if not links:
            return ""

        # Prefer PMC links
        pmc_links = [l for l in links if l['type'] == 'pmc']
        if pmc_links:
            return self.scrape_pmc_full_text(pmc_links[0]['url'])

        return ""

    def scrape_all_articles(self, search_url, pages=3):
        """Main method to scrape all articles from PubMed search"""
        pmids = self.extract_pmids_from_search(search_url, pages)
        if not pmids:
            print("No PMIDs found!")
            return []

        for i, pmid in enumerate(pmids, 1):
            print(f"\nProcessing article {i}/{len(pmids)}: PMID {pmid}")
            article_data = self.get_article_details(pmid)
            if not article_data:
                continue
            self.find_full_text_links(pmid, article_data)
            article_data['full_text_content'] = self.get_full_text_content(article_data)
            self.scraped_data.append(article_data)
            print(f"Completed {i}/{len(pmids)} articles")

        return self.scraped_data

    def save_data(self, filename_base="pubmed_articles"):
        if not self.scraped_data:
            print("No data to save!")
            return

        # JSON
        with open(f"{filename_base}.json", 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, indent=2, ensure_ascii=False)
        print(f"Data saved to {filename_base}.json")

        # CSV
        with open(f"{filename_base}.csv", 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['pmid', 'title', 'authors', 'journal', 'publication_date', 'abstract', 'doi', 'url', 'full_text_links_count', 'full_text_available']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for article in self.scraped_data:
                writer.writerow({
                    'pmid': article['pmid'],
                    'title': article['title'],
                    'authors': '; '.join(article['authors']),
                    'journal': article['journal'],
                    'publication_date': article['publication_date'],
                    'abstract': (article['abstract'][:500] + '...') if len(article['abstract']) > 500 else article['abstract'],
                    'doi': article['doi'],
                    'url': article['url'],
                    'full_text_links_count': len(article.get('full_text_links', [])),
                    'full_text_available': 'Yes' if article.get('full_text_content') else 'No'
                })
        print(f"Data saved to {filename_base}.csv")
        
if __name__ == "__main__":
    scraper = PubMedScraper(delay=3)
    search_url="https://pubmed.ncbi.nlm.nih.gov/?term=muscle+hypertrophy&filter=simsearch2.ffrft&filter=years.2010-2025&size=200"
    scraper.scrape_all_articles(search_url, pages=3)
    scraper.save_data("muscle_hypertrophy_articles")