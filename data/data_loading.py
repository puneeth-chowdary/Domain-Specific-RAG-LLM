import json
import csv
import sys
import os

#sys.path.append(os.path.abspath("users/reddeppakollu/puneeth/project_r/llm"))


from llm.odm import Article



def load_articles_from_json(json_file_path: str):
    """Load articles from JSON file with your exact format"""
    with open(json_file_path, 'r') as f:
        articles_data = json.load(f)
    
    article_documents = []
    for article_data in articles_data:
        article = Article(
            pmid=str(article_data['pmid']),  # Ensure string type
            title=article_data['title'],
            authors=article_data['authors'],  # Keep as string
            url=article_data['url'],
            content=article_data['content']
        )
        article_documents.append(article)
    
    # Bulk insert into MongoDB
    success = Article.bulk_insert(article_documents)
    
    if success:
        print(f"✅ Successfully loaded {len(article_documents)} articles")
        
        # Verify count
        stored_count = len(Article.find_all())
        print(f"📊 Total articles in database: {stored_count}")
    else:
        print("❌ Failed to load articles")

def load_articles_from_csv(csv_file_path: str):
    """Load articles from CSV file with your exact format"""
    articles = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            article = Article(
                pmid=str(row['pmid']),
                title=row['title'],
                authors=row['authors'],  # Keep as string
                url=row['url'],
                content=row['content']
            )
            articles.append(article)
    
    # Bulk insert
    success = Article.bulk_insert(articles)
    
    if success:
        print(f"✅ Successfully loaded {len(articles)} articles from CSV")
    else:
        print("❌ Failed to load articles from CSV")

def search_articles():
    """Example search functionality"""
    # Find all articles
    all_articles = Article.find_all()
    print(f"Total articles: {len(all_articles)}")
    
    # Find articles by PMID
    specific_article = Article.find_one(pmid="12345678")
    if specific_article:
        print(f"Found article: {specific_article.title}")
        print(f"Authors: {specific_article.authors}")  # This will be a string

def export_articles_to_json(output_file: str):
    """Export all articles back to JSON format"""
    articles = Article.find_all()
    
    # Convert to list of dictionaries
    articles_data = []
    for article in articles:
        article_data = {
            "pmid": article.pmid,
            "title": article.title,
            "authors": article.authors,  # Still string format
            "url": article.url,
            "content": article.content
        }
        articles_data.append(article_data)
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(articles_data, f, indent=2)
    
    print(f"✅ Exported {len(articles_data)} articles to {output_file}")

if __name__ == "__main__":
    load_articles_from_json("scraped_articles.json")  # If JSON
