# llm/embedding/service.py
from sentence_transformers import SentenceTransformer
from typing import List, Dict

class EmbeddingService:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.embedding_size = self.model.get_sentence_embedding_dimension()
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for single text"""
        return self.model.encode(text).tolist()
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings in batch"""
        return self.model.encode(texts).tolist()

class ArticleEmbeddingHandler:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.embedding_service = EmbeddingService(model_name)
        self.model_name = model_name
    
    def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Add embeddings to chunks"""
        if not chunks:
            return []
        
        chunk_texts = [chunk['chunk_content'] for chunk in chunks]
        embeddings = self.embedding_service.embed_batch(chunk_texts)
        
        embedded_chunks = []
        for i, chunk in enumerate(chunks):
            embedded_chunk = chunk.copy()
            embedded_chunk['embedding'] = embeddings[i]
            embedded_chunk['embedding_model'] = self.model_name
            embedded_chunk['embedding_size'] = len(embeddings[i])
            embedded_chunks.append(embedded_chunk)
        
        return embedded_chunks