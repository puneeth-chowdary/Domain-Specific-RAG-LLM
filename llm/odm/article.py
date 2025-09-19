from typing import List, Optional
from pydantic import Field
from .base import BaseDocument  # This should work now

class Article(BaseDocument):
    pmid: str
    title: str
    authors: str
    url: str
    content: str
    journal: Optional[str] = None
    publication_date: Optional[str] = None
    abstract: Optional[str] = None
    doi: Optional[str] = None
    
    def get_authors_list(self) -> List[str]:
        """Convert authors string to list if needed"""
        if not self.authors:
            return []
        return [author.strip() for author in self.authors.split(',')]
    
    def get_citation(self) -> str:
        authors_str = self.authors if self.authors else "Unknown authors"
        return f"{authors_str}. {self.title}. {self.journal or 'Unknown journal'} {self.publication_date or ''}"