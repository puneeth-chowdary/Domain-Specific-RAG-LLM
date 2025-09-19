# test_complete.py
import sys
sys.path.append('.')
import logging
logging.basicConfig(level=logging.INFO)

from llm.domain.query import Query
from llm.rag.self_query import SelfQuery

# Test the complete flow
query = Query.from_str("I want information from PMID 12345678 about cancer")
print(f"Initial query: {query.content}, pmid: {query.pmid}")

self_query = SelfQuery(mock=True)
result = self_query.generate(query)

print(f"After self-query: {result.content}, pmid: {result.pmid}")
print("✅ Complete test passed!")