"""Ollama LLM Service"""

from typing import Iterator

from langchain_ollama import OllamaLLM

from app.services.llm.base import BaseLLM
from app.core.config import config


class OllamaModel(BaseLLM):
    """Ollama LLM Service"""

    def __init__(self, model: str, base_url: str = "http://localhost:11434"):
        self.model = model or config.OLLAMA_MODEL
        self.base_url = base_url or config.OLLAMA_BASE_URL

    def load_model(self) -> None:
        """Load Ollama Model"""

        self.llm = OllamaLLM(model=self.model, base_url=self.base_url)

    def invoke(self, prompt: str) -> str:
        """Generate response from prompt"""

        response = self.llm.invoke(prompt)
        return response

    def stream(self, prompt: str) -> Iterator[str]:
        """Generate stream of resposne"""

        for chunk in self.llm.stream(prompt):
            if chunk:
                yield chunk
