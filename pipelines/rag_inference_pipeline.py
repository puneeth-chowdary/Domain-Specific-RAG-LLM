import logging
from typing import List
from llm.rag.retriever import ContextRetriever
from llm.llm_api.client import LLMClient

#logger = logging.getLogger(__name__)

class RAGInferencePipeline:
    def __init__(self, mock: bool = False, model_name: str = "LiquidAI/LFM2-1.2B",
                 embedding_model="sentence-transformers/all-MiniLM-L6-v2", trust_remote_code: bool = True):
        self.retriever = ContextRetriever(mock=mock)
        if not mock:
            self.llm_client = LLMClient(model_name=model_name)
        self.mock = mock
    
    def generate_response(self, query: str) -> str:
        # Retrieving relevantent context 
        context_chunks = self.retriever.search(query, k=3)
        
        # Build prompt with context
        prompt = self._build_prompt(query, context_chunks)
        
        if self.mock:
            return ("Based on the provided PubMed context, I can provide information about this topic. "
                    "The research indicates that this is an important area of study with several recent developments.")
        response = self.llm_client.generate_completion(
            prompt,
            max_new_tokens=2048,
            temperature=0.3 
        )
        
        return response
    
    def _build_prompt(self, query: str, context_chunks: List[dict]) -> str:
        if not context_chunks:
            return f"Question: {query}\nAnswer:"
        
        context_str = "\n".join([
            f"Source: {chunk.get('title', 'Unknown')} - PMID: {chunk.get('pmid', 'Unknown')}\n"
            f"Content: {chunk.get('chunk_content', '')}\n"
            for chunk in context_chunks
        ])

        return f"""Based on the following context information from PubMed articles, answer the user's question.

Context:
{context_str}

Question: {query}

Answer:"""
