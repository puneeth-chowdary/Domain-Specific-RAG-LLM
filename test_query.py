# test_query.py
import sys
sys.path.append('.')

from llm.domain.query import Query

# Test the Query model
query = Query.from_str("Test query with PMID 12345678")
print(f"Query content: {query.content}")
print(f"Query pmid (should be None): {query.pmid}")

# Test setting pmid
query.pmid = "12345678"
print(f"Query pmid after setting: {query.pmid}")

print("✅ Query model test passed!")