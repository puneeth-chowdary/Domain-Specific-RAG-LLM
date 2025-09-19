# llm/rag/reranking.py 
#advanced answering
import logging
from typing import List
from llm.domain.query import Query
from llm.rag.base import RAGStep
from rank_bm25 import BM25Okapi

#logger = logging.getLogger(__name__)

class Reranker(RAGStep):
    def __init__(self, mock: bool = False) -> None:
        super().__init__(mock=mock)
        self._model = None  
    
    def generate(self, query: Query, chunks: List[dict], keep_top_k: int) -> List[dict]:
        if self._mock:

            return chunks[:keep_top_k]
        

        tokenized_chunks = [chunk.get("chunk_content", "").lower().split() for chunk in chunks]

        bm25 = BM25Okapi(tokenized_chunks)
        tokenized_query = query.content.lower().split()
        scores = bm25.get_scores(tokenized_query)
        scored_chunks = list(zip(scores, chunks))
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        
        return [chunk for _, chunk in scored_chunks[:keep_top_k]]
