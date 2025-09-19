# llm/domain/query.py
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import Optional, List
import datetime

class Query(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    content: str
    pmid: Optional[str] = None  
    metadata: dict = Field(default_factory=dict)
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.now)

    @classmethod
    def from_str(cls, query_str: str) -> "Query":
        return Query(content=query_str.strip())
    
    def replace_content(self, new_content: str) -> "Query":
        return Query(
            id=self.id,
            content=new_content,
            pmid=self.pmid,  
            metadata=self.metadata,
            created_at=self.created_at
        )

class EmbeddedQuery(Query):
    embedding: List[float]