# llm/chunking/handlers.py
import re
from typing import List, Dict
import hashlib

class ArticleChunkingHandler:
    def __init__(self, chunk_size=1000, chunk_overlap=200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def chunk(self, cleaned_article: Dict) -> List[Dict]:
        """Split article content into chunks while preserving metadata"""
        content = cleaned_article.get('content', '')
        if not content:
            return []
        

        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk.strip():
                    chunks.append(self._create_chunk(cleaned_article, current_chunk.strip()))
                current_chunk = sentence + " "
        
        if current_chunk.strip():
            chunks.append(self._create_chunk(cleaned_article, current_chunk.strip()))
        
        return chunks
    
    def _create_chunk(self, article: Dict, chunk_content: str) -> Dict:
        """Create chunk document matching your Qdrant payload structure"""
        chunk_id = hashlib.md5(chunk_content.encode()).hexdigest()
        
        return {

            'pmid': article.get('pmid', ''),
            'chunk_content': chunk_content,
            'title': article.get('title', ''),
            'authors': article.get('authors', ''),
            'url': article.get('url', ''),
            'metadata': {
                'chunk_size': len(chunk_content),
                'original_length': len(article.get('content', '')),
                'chunk_id': chunk_id
            }
        }