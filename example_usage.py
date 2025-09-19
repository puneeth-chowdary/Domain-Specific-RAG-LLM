# example_usage.py
import logging
import argparse
from pipelines.rag_inference_pipeline import RAGInferencePipeline

# Set up logging
logging.basicConfig(level=logging.INFO)

def main():
    parser = argparse.ArgumentParser(description='RAG Pipeline with Hugging Face Models')
    parser.add_argument('--mock', action='store_true', help='Use mock mode (no real LLM calls)')
    parser.add_argument('--model', type=str, default="apple/FastVLM-1.7B", 
                       help='Hugging Face model name')
    parser.add_argument('--embedding_model', type=str, default="sentence-transformers/all-MiniLM-L6-v2", 
                        help='SentenceTransformer model for embeddings')
    parser.add_argument('--query', type=str, help='Query to process')
    
    args = parser.parse_args()
    pipeline = RAGInferencePipeline(mock=args.mock, model_name=args.model,trust_remote_code=True)
    
    if args.query:
        # Processing  single query
        print(f"Query: {args.query}")
        response = pipeline.generate_response(args.query)
        print(f"Response: {response}")
    else:
        # Demo
        example_queries = [
            "explain what are the major contributors for muscle growth in regions like biceps,tricpes and shoulders, generate a clear and structed answer"
            #"what are the latest advancements in muscle hypetrophy?",
            #"tell me about the article with pmid 35389932 ",
            #"how does creatine supplementation affect muscle growth?",
            #"explain the role of protein intake in muscle hypertrophy"
        ]
        
        for query in example_queries:
            print(f"\nQuery: {query}")
            response = pipeline.generate_response(query)
            print(f"Response: {response}")

if __name__ == "__main__":
    main()