# pipelines/rag_feature_pipeline.py
from llm.cleaning.handlers import ArticleCleaningHandler
from llm.chunking.handlers import ArticleChunkingHandler
from llm.embedding.service import ArticleEmbeddingHandler
from llm.vector_store.qdrant_client import QdrantVectorStore, ArticleVectorMapper
from llm.odm import Article
import time
class RAGFeaturePipeline:
    def __init__(self, batch_size=50):
        self.cleaning_handler = ArticleCleaningHandler()
        self.chunking_handler = ArticleChunkingHandler()
        self.embedding_handler = ArticleEmbeddingHandler()
        self.vector_store = QdrantVectorStore(batch_size=batch_size)
        self.vector_mapper = ArticleVectorMapper()
    
    def run(self):
        """Run complete RAG pipeline with better error handling"""
        print("🚀 Starting RAG Feature Pipeline...")
        try:
            print("📥 Extracting articles from MongoDB...")
            articles = Article.find_all()
            
            print(f"📊 Found {len(articles)} articles")
            
            all_embedded_chunks = []
            
            for i, article in enumerate(articles):
                try:
                    article_dict = article.to_mongo()
                    print(f"🧹 Cleaning article {i+1}/{len(articles)}: {article_dict.get('title', 'Unknown')[:50]}...")
                    cleaned_article = self.cleaning_handler.clean(article_dict)
                    print("✂️ Chunking article...")
                    chunks = self.chunking_handler.chunk(cleaned_article)
                    if chunks:
                        print("🔢 Generating embeddings...")
                        embedded_chunks = self.embedding_handler.embed_chunks(chunks)
                        all_embedded_chunks.extend(embedded_chunks)
                        print(f"📦 Processed article with {len(chunks)} chunks")
                    else:
                        print("⚠️ No chunks generated for this article")
                    time.sleep(0.1)
                except Exception as e:
                    print(f"❌ Error processing article {i+1}: {e}")
                    continue
            if all_embedded_chunks:
                print(f"🗄️ Loading {len(all_embedded_chunks)} chunks to Qdrant in batches...")
                points = [self.vector_mapper.to_point_struct(chunk) for chunk in all_embedded_chunks]
                self.vector_store.create_collection(
                    collection_name="article_chunks",
                    vector_size=384 
                )
                self.vector_store.upsert_vectors("article_chunks", points)
                print(f"✅ Pipeline completed! Loaded {len(points)} chunks to Qdrant")
                return len(points)
            else:
                print("❌ No chunks to load into Qdrant")
                return 0
        except Exception as e:
            print(f"💥 Pipeline failed: {e}")
            import traceback
            traceback.print_exc()
            return 0
if __name__ == "__main__":
    pipeline = RAGFeaturePipeline(batch_size=50)  
    pipeline.run()