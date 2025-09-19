# llm/rag/self_query.py 
import logging
import re
from llm.domain.query import Query
from llm.rag.base import RAGStep, PromptTemplateFactory

#logger = logging.getLogger(__name__)

class SelfQueryTemplate(PromptTemplateFactory):
    def create_template(self) -> str:
        return """Extract the PubMed ID (PMID) from the following query. 
Return only the numeric PMID if found, otherwise return 'none'.

Examples:
Query: "What does PMID 12345678 say about cancer?"
Response: 12345678

Query: "Tell me about recent developments in Alzheimer's research"
Response: none

Query: "I'm looking for information from article PMID 87654321 about diabetes"
Response: 87654321

Query: {question}
Response:"""

class SelfQuery(RAGStep):
    def generate(self, query: Query) -> Query:
        if self._mock:
            pmid = self._extract_pmid_with_regex(query.content)
            if pmid:
                query.pmid = pmid
                query.metadata["extracted_pmid"] = pmid
            return query
            
        template = SelfQueryTemplate().create_template()
        prompt = template.format(question=query.content)
        pmid = self._extract_pmid_with_regex(query.content)
        if pmid:
            query.pmid = pmid
            query.metadata["extracted_pmid"] = pmid
            
        return query
    
    def _extract_pmid_with_regex(self, text: str) -> str:
        """Extract PMID using regex patterns"""
        patterns = [
            r"pmid[: ]*(\d+)",
            r"PMID[: ]*(\d+)",
            r"pubmed[: ]*(\d+)",
            r"PubMed[: ]*(\d+)",
            r"article[: ]*(\d+)",
            r"reference[: ]*(\d+)",
            r"(\d{7,8})"  #general pattern for 7-8 digit numbers pmid format 
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return None