"""Abstract Class for LLM Services"""

from typing import Any, Iterator
from abc import ABC, abstractmethod

class BaseLLM(ABC):
    """Abstract class for llm services"""
    
    @abstractmethod
    def load_model(self) -> None:
        """Load Model"""

    @abstractmethod
    def invoke(self, prompt: str, **Kwargs: Any) -> str:
        """Generate a response from prompt"""
    
    @abstractmethod
    def stream(self, prompt: str, **Kwargs: Any) -> Iterator[str]:
        """Generate response in stream"""
        
