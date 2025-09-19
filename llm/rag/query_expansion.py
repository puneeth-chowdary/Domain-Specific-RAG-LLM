# llm/rag/query_expansion.py
import logging
from typing import List
from llm.domain.query import Query
from llm.rag.base import RAGStep, PromptTemplateFactory
from llm.llm_api.client import LLMClient

#logger = logging.getLogger(__name__)

class QueryExpansionTemplate(PromptTemplateFactory):
    separator = "#next-query#"
    
    def create_template(self, expand_to_n: int) -> str:
        return (
            f"You are an AI language model assistant. "
            f"Your task is to generate {expand_to_n} diverse rephrasings of the given user question "
            f"to retrieve relevant documents from a vector database. "
            f"Ensure the alternatives preserve the meaning but vary in phrasing, terminology, or focus. "
            f"Provide the alternative questions separated by '{self.separator}'. "
            f"Original question: {{question}}"
        )

class QueryExpansion(RAGStep):
    def __init__(self, mock: bool = False, model_name: str = "LiquidAI/LFM2-1.2B") -> None:
        super().__init__(mock)
        if not mock:
            self.llm_client = LLMClient(model_name=model_name)
    
    def generate(self, query: Query, expand_to_n: int) -> List[Query]:
        if self._mock:
            return [query for _ in range(expand_to_n)]
        
        template = QueryExpansionTemplate().create_template(expand_to_n)
        prompt = template.format(question=query.content)
        

        response = self.llm_client.generate_completion(
            prompt, 
            max_new_tokens=512,   
            temperature=0.3,      
            top_p=0.9,      
            repetiton_penalty=1.05  
        )
        
        queries_content = [
            q.strip() for q in response.strip().split(QueryExpansionTemplate.separator)
            if q.strip()
        ]

        queries = [query]
        seen = {query.content.lower()}
        for content in queries_content:
            if content.lower() not in seen:
                queries.append(query.replace_content(content))
                seen.add(content.lower())
            if len(queries) >= expand_to_n:
                break
        
        while len(queries) < expand_to_n:
            queries.append(query)
        
        return queries[:expand_to_n]
