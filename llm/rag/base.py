# llm/rag/base.py
from abc import ABC, abstractmethod
from typing import Any
from llm.domain.query import Query

class RAGStep(ABC):
    def __init__(self, mock: bool = False) -> None:
        self._mock = mock
    
    @abstractmethod
    def generate(self, query: Query, *args, **kwargs) -> Any:
        pass

class PromptTemplateFactory(ABC):
    @abstractmethod
    def create_template(self) -> str:
        pass