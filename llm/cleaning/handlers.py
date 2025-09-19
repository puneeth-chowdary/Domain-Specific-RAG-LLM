# llm/cleaning/handlers.py
import re
from typing import Dict

def clean_text(text: str) -> str:
    """Clean text for embedding models"""
    if not text:
        return ""
    text = re.sub(r'http\S+', '[URL]', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    text = ' '.join(text.split())
    
    return text

class ArticleCleaningHandler:
    def clean(self, article_dict: Dict) -> Dict:
        """Clean article content while preserving your data format"""
        cleaned_article = article_dict.copy()
        cleaned_article['content'] = clean_text(article_dict.get('content', ''))

        cleaned_article['title'] = clean_text(article_dict.get('title', ''))
        
        
        return cleaned_article