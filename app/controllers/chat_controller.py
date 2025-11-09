"""Controller for chat"""

from typing import Iterator
from app.services.llm.factory import get_llm_instance

class ChatController:
    """Controller for chat"""
    
    def __init__(self, model_name: str = "ollama/llama2"):
        self.model_name = model_name
        self.llm = get_llm_instance(model_name)
        
    def chat(self, query: str) -> str:
        """chat service"""
        
        return self.llm.invoke(query)
    
    def chat_stream(self, query: str) -> Iterator[str]:
        """chat stream service"""
        
        return self.llm.stream(query)
        
        