#interactive chat with conversation memory and cleanup after chat ends 

import logging
import argparse
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pipelines.rag_inference_pipeline import RAGInferencePipeline
from llm.vector_store.qdrant_client import QdrantVectorStore
from llm.embedding.service import EmbeddingService
from llm.llm_api.client import LLMClient
from llm.domain.query import Query
from qdrant_client import models

# Set up logging
logging.basicConfig(level=logging.INFO)

class ConversationManager:
    """Manages conversation history using Qdrant vector store with automatic cleanup"""
    
    def __init__(self, collection_name: str = "conversation_history"):
        self.vector_store = QdrantVectorStore()
        self.embedding_service = EmbeddingService()
        self.collection_name = collection_name
        self._init_conversation_collection()
    
    def _init_conversation_collection(self):
        """Initialize the conversation history collection"""
        try:
            self.vector_store.client.get_collection(self.collection_name)
            logging.info(f"Conversation collection '{self.collection_name}' already exists")
        except Exception:
            self.vector_store.create_collection(
                self.collection_name, 
                self.embedding_service.embedding_size
            )
            logging.info(f"Created conversation collection '{self.collection_name}'")
    
    def add_to_conversation(self, session_id: str, query: str, response: str):
        """Add a query-response pair to the conversation history"""
        query_embedding = self.embedding_service.embed_text(query)
        
        point = models.PointStruct(
            id=str(uuid.uuid4()),
            vector=query_embedding,
            payload={
                "session_id": session_id,
                "query": query,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        self.vector_store.upsert_vectors(self.collection_name, [point])
    
    def get_conversation_context(self, session_id: str, current_query: str, limit: int = 3) -> str:
        """Retrieve relevant conversation history for the current query"""
        query_embedding = self.embedding_service.embed_text(current_query)
        
        results = self.vector_store.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="session_id",
                        match=models.MatchValue(value=session_id)
                    )
                ]
            ),
            limit=limit
        )
        
        if not results:
            return ""
            
        context = "Previous conversation context:\n"
        for i, result in enumerate(results):
            context += f"{i+1}. User: {result.payload['query']}\n"
            context += f"   Assistant: {result.payload['response']}\n\n"
        
        return context
    
    def clear_session_history(self, session_id: str):
        """Clear all conversation history for a specific session"""
        self.vector_store.client.delete(
            collection_name=self.collection_name,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="session_id",
                            match=models.MatchValue(value=session_id)
                        )
                    ]
                )
            )
        )
        logging.info(f"Cleared conversation history for session: {session_id}")

class EnhancedRAGChat:
    """Enhanced RAG chat system with conversation memory and automatic cleanup"""
    
    def __init__(self, model_name: str = "LiquidAI/LFM2-1.2B", mock: bool = False, trust_remote_code: bool = False):
        self.conversation_manager = ConversationManager()
        self.rag_pipeline = RAGInferencePipeline(mock=mock, model_name=model_name, trust_remote_code=trust_remote_code)
        self.session_id = str(uuid.uuid4())
        logging.info(f"Started new conversation session: {self.session_id}")
    
    def _build_enhanced_prompt(self, query: str, conversation_context: str) -> str:
        """Builds prompt with conversation history"""
        if not conversation_context:
            return query 
        
        enhanced_prompt = f"{conversation_context}\n\nBased on our previous conversation, please answer this new question:\n\n{query}"
        return enhanced_prompt
    
    def chat(self, query: str) -> str:
        """Process a query with conversation context"""
        conversation_context = self.conversation_manager.get_conversation_context(
            self.session_id, query, limit=2
        )

        enhanced_query = self._build_enhanced_prompt(query, conversation_context)

        response = self.rag_pipeline.generate_response(enhanced_query)
        
        self.conversation_manager.add_to_conversation(
            self.session_id, query, response
        )
        
        return response
    
    def end_session(self):
        """End the current session and clean up conversation history"""
        self.conversation_manager.clear_session_history(self.session_id)
        logging.info(f"Ended session: {self.session_id}")
    
    def multi_turn_chat(self):
        """Run a multi-turn chat interface with automatic cleanup"""
        print("Welcome to the Enhanced RAG Chat System!")
        print("Type 'quit' to exit, 'clear' to start a new conversation session.")
        print("-" * 50)
        
        try:
            while True:
                user_input = input("You: ").strip()
                
                if user_input.lower() == 'quit':
                    print("Ending conversation and cleaning up...")
                    break
                
                if user_input.lower() == 'clear':
                    self.end_session()
                    self.session_id = str(uuid.uuid4())
                    print(f"Started new conversation session: {self.session_id}")
                    continue
                
                if not user_input:
                    continue
                response = self.chat(user_input)
                
                print(f"Assistant: {response}")
                print("-" * 50)
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        finally:
            self.end_session()

def main():
    parser = argparse.ArgumentParser(description='RAG Pipeline with Hugging Face Models')
    parser.add_argument('--mock', action='store_true', help='Use mock mode (no real LLM calls)')
    parser.add_argument('--model', type=str, default="LiquidAI/LFM2-1.2B", 
                       help='Hugging Face model name')
    parser.add_argument('--embedding_model', type=str, default="sentence-transformers/all-MiniLM-L6-v2", 
                        help='SentenceTransformer model for embeddings')
    parser.add_argument('--query', type=str, help='Query to process')
    parser.add_argument('--interactive', action='store_true', help='Start interactive chat session')
    parser.add_argument('--trust_remote_code', action='store_true', help='Trust remote code for model loading')
    
    args = parser.parse_args()
    
    if args.interactive or not args.query:
        # Start interactive chat session
        chat_system = EnhancedRAGChat(
            model_name=args.model,
            mock=args.mock,
            trust_remote_code=args.trust_remote_code
        )
        chat_system.multi_turn_chat()
    else:
        # Process single query
        pipeline = RAGInferencePipeline(
            mock=args.mock, 
            model_name=args.model,
            trust_remote_code=args.trust_remote_code
        )
        
        print(f"Query: {args.query}")
        response = pipeline.generate_response(args.query)
        print(f"Response: {response}")

if __name__ == "__main__":
    main()