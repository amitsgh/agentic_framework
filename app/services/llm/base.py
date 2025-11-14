"""Abstract Class for LLM Services"""

from typing import List, Dict, Iterator
from abc import ABC, abstractmethod


class BaseLLM(ABC):
    """Abstract class for llm services"""

    @abstractmethod
    def load_model(self):
        """Initialize the LLM"""

    @abstractmethod
    def model_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate a response"""

    @abstractmethod
    def model_stream_response(self, messages: List[dict]) -> Iterator[str]:
        """Generate response in stream"""
