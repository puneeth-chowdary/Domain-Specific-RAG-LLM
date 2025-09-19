import concurrent.futures
from typing import List
from llm.domain.query import Query
from llm.rag.query_expansion import QueryExpansion
from llm.rag.self_query import SelfQuery
from llm.rag.reranking import Reranker
from llm.embedding.service import EmbeddingService
from llm.vector_store.qdrant_client import QdrantVectorStore


class ContextRetriever:
    def __init__(self, mock: bool = False) -> None:
        self._query_expander = QueryExpansion(mock=mock)
        self._metadata_extractor = SelfQuery(mock=mock)
        self._reranker = Reranker(mock=mock)
        self._embedding_service = EmbeddingService()
        self._vector_store = QdrantVectorStore()
    
    def search(self, query: str, k: int = 3, expand_to_n_queries: int = 3) -> List[dict]:
        query_model = Query.from_str(query)
        
        query_model = self._metadata_extractor.generate(query_model)
        
        expanded_queries = self._query_expander.generate(query_model, expand_to_n_queries)
        
        with concurrent.futures.ThreadPoolExecutor() as executor:
            search_tasks = [
                executor.submit(self._search_single_query, query, k)
                for query in expanded_queries
            ]
            
            # Collect results
            all_chunks = []
            for future in concurrent.futures.as_completed(search_tasks):
                try:
                    chunks = future.result()
                    all_chunks.extend(chunks)
                except Exception:
                    pass
        #deduplicate chunks 
        unique_chunks = self._deduplicate_chunks(all_chunks)
        
        if unique_chunks:
            ranked_chunks = self._reranker.generate(query_model, unique_chunks, k)
            return ranked_chunks
        else:
            return []
    
    def _search_single_query(self, query: Query, k: int) -> List[dict]:
        #query embedding 
        query_embedding = self._embedding_service.embed_text(query.content)
        
        # Using pmid for filteting if pmid is given in query 
        pmid_filter = query.pmid
        
        # Searching in  vector store
        search_results = self._vector_store.search_similar(
            collection_name="article_chunks",
            query_vector=query_embedding,
            limit=k * 3, 
            pmid_filter=pmid_filter
        )
        
        return search_results
    
    def _deduplicate_chunks(self, chunks: List[dict]) -> List[dict]:
        seen = set()
        unique_chunks = []
        
        for chunk in chunks:
            content = chunk.get("chunk_content", "")
            if content not in seen:
                seen.add(content)
                unique_chunks.append(chunk)
        
        return unique_chunks
