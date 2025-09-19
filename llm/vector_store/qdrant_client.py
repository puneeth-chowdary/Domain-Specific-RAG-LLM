# llm/vector_store/qdrant_client.py
from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict, Optional
import uuid
import time
from tenacity import retry, stop_after_attempt, wait_exponential

class QdrantVectorStore:
    def __init__(self, host="localhost", port=6333, batch_size=100, timeout=30):
        self.client = QdrantClient(
            host=host, 
            port=port,
            timeout=timeout
        )
        self.batch_size = batch_size
    
    def create_collection(self, collection_name: str, vector_size: int):
        """Create Qdrant collection"""
        try:
            self.client.recreate_collection(
                collection_name=collection_name,
                vectors_config=models.VectorParams(
                    size=vector_size,
                    distance=models.Distance.COSINE
                )
            )
            print(f"✅ Created collection: {collection_name}")
        except Exception as e:
            print(f"⚠️  Collection may already exist: {e}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def upsert_vectors(self, collection_name: str, points: List[models.PointStruct]):
        """Insert vectors into Qdrant with retry and batching"""
        if not points:
            return
        
        # Process in batches to avoid timeout
        for i in range(0, len(points), self.batch_size):
            batch = points[i:i + self.batch_size]
            try:
                self.client.upsert(
                    collection_name=collection_name,
                    points=batch,
                    wait=True
                )
                print(f"✅ Inserted batch {i//self.batch_size + 1}: {len(batch)} points")
                time.sleep(0.1)  # Small delay between batches
            except Exception as e:
                print(f"❌ Failed to insert batch {i//self.batch_size + 1}: {e}")
                raise
    
    def search_similar(
        self, 
        collection_name: str, 
        query_vector: List[float], 
        limit: int = 10,
        pmid_filter: Optional[str] = None
    ) -> List[Dict]:
        """Search for similar vectors with optional pmid filtering"""
        # Create filter if pmid is provided
        qdrant_filter = None
        if pmid_filter:
            qdrant_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="pmid",
                        match=models.MatchValue(value=pmid_filter)
                    )
                ]
            )
        
        # Perform the search
        results = self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True
        )
        
        # Convert to list of dictionaries with consistent format
        return [
            {
                "id": result.id,
                "score": result.score,
                "payload": result.payload,
                "chunk_content": result.payload.get("chunk_content", ""),
                "pmid": result.payload.get("pmid", ""),
                "title": result.payload.get("title", ""),
                "authors": result.payload.get("authors", ""),
                "url": result.payload.get("url", ""),
                "embedding_model": result.payload.get("embedding_model", ""),
                "chunk_metadata": result.payload.get("chunk_metadata", {})
            }
            for result in results
        ]
    
    def get_collection_info(self, collection_name: str) -> Optional[Dict]:
        """Get information about a collection"""
        try:
            return self.client.get_collection(collection_name)
        except Exception as e:
            print(f"❌ Failed to get collection info: {e}")
            return None
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection"""
        try:
            self.client.delete_collection(collection_name)
            print(f"✅ Deleted collection: {collection_name}")
            return True
        except Exception as e:
            print(f"❌ Failed to delete collection: {e}")
            return False

class ArticleVectorMapper:
    """Object-Vector Mapper for article chunks with your data format"""
    
    @staticmethod
    def to_point_struct(embedded_chunk: Dict) -> models.PointStruct:
        """Convert embedded chunk to Qdrant point with your exact payload structure"""
        return models.PointStruct(
            id=str(uuid.uuid4()),
            vector=embedded_chunk['embedding'],
            payload={
                'pmid': embedded_chunk['pmid'],
                'chunk_content': embedded_chunk['chunk_content'],
                'title': embedded_chunk['title'],
                'authors': embedded_chunk['authors'],
                'url': embedded_chunk['url'],
                'embedding_model': embedded_chunk['embedding_model'],
                'chunk_metadata': embedded_chunk.get('metadata', {})
            }
        )
    
    @staticmethod
    def from_point_struct(point: models.ScoredPoint) -> Dict:
        """Convert Qdrant point back to article chunk format"""
        return {
            'id': point.id,
            'embedding': point.vector,
            'pmid': point.payload.get('pmid'),
            'chunk_content': point.payload.get('chunk_content'),
            'title': point.payload.get('title'),
            'authors': point.payload.get('authors'),
            'url': point.payload.get('url'),
            'embedding_model': point.payload.get('embedding_model'),
            'metadata': point.payload.get('chunk_metadata', {}),
            'score': point.score
        }