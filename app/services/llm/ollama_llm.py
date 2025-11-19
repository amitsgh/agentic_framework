"""Ollama LLM Service"""

from typing import List, Dict, Iterator

import ollama
from ollama import Client

from app.services.llm.base import BaseLLM
from app.exceptions import LLMError
from app.config import config
from app.utils.logger import setuplog

logger = setuplog(__name__)


class OllamaModel(BaseLLM):
    """Ollama LLM Service"""

    def __init__(self, model: str, base_url: str | None = None):
        self.model = model or config.OLLAMA_MODEL
        self.base_url = base_url or config.OLLAMA_BASE_URL
        self._client = None
        self._model_loaded = False

    def load_model(self) -> None:
        """Initialize Ollama model"""

        if self._model_loaded:
            logger.debug("Model %s already loaded", self.model)
            return

        try:
            if self.base_url:
                self._client = Client(host=self.base_url)
            else:
                self._client = Client()

            logger.info(
                "Loading Ollama model: %s at %s", self.model, self.base_url or "default"
            )

            try:
                models = ollama.list()
                model_names = [m["name"] for m in models.get("models", [])]
                if self.model not in model_names:
                    logger.warning(
                        "Model %s not found locally. It will be pulled on first use.",
                        self.model,
                    )

            except Exception as e:
                logger.warning("Could not verify model existence: %s", str(e))

            self._model_loaded = True
            logger.info("Ollama model %s initialized successfully", self.model)

        except Exception as e:
            logger.critical("Failed to load Ollama model: %s", str(e), exc_info=True)
            logger.debug(
                "Ollama model load failed for model: %s at %s",
                self.model,
                self.base_url,
            )
            raise LLMError(f"Failed to load Ollama model: {str(e)}") from e

    def model_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate response"""

        if not self._model_loaded:
            self.load_model()

        if not self._client:
            raise LLMError(
                "Ollama client is not initialized. Failed to connect or load model"
            )

        logger.info("Invoking Ollama chat model: %s", self.model)
        logger.debug("Chat request with %d messages", len(messages))

        try:
            response = self._client.chat(
                model=self.model,
                messages=messages,
            )

            if isinstance(response, dict):
                message = response.get("message", {})
                content = message.get("content", "")
                logger.debug("Received response of length: %d", len(content))
                return content

            logger.error("Unexpected response format: %s", type(response))
            raise LLMError(f"Unexpected response format: {type(response)}")

        except Exception as e:
            logger.error(
                "Error generating response with Ollama chat: %s", str(e), exc_info=True
            )
            logger.debug(
                "Chat error for model: %s, message count: %d", self.model, len(messages)
            )
            raise LLMError(f"Error generating response: {str(e)}") from e

    def model_stream_response(self, messages: List[dict]) -> Iterator[str]:
        """Generate stream of response"""

        if not self._model_loaded:
            self.load_model()

        if not self._client:
            raise RuntimeError(
                "Ollama client is not initialized. Failed to connect or load model"
            )

        logger.info("Invoking Ollama chat model: %s", self.model)
        logger.info("Invoking Ollama model: %s at %s", self.model, self.base_url)
        logger.debug("Stream chat request with %d messages", len(messages))

        try:
            response = self._client.chat(
                model=self.model, messages=messages, stream=True
            )
            chunk_count = 0
            for chunk in response:
                if isinstance(chunk, dict):
                    message = chunk.get("message", {})
                    token = message.get("content", "")
                    if token:
                        chunk_count += 1
                        if chunk_count % 10 == 0:  # Log every 10 chunks to avoid spam
                            logger.debug("Streaming chunk %d...", chunk_count)
                        yield token
                else:
                    if chunk:
                        chunk_count += 1
                        yield str(chunk)
            logger.debug("Stream completed: %d chunks yielded", chunk_count)

        except Exception as e:
            logger.error(
                "Error generating stream response with Ollama chat: %s",
                str(e),
                exc_info=True,
            )
            logger.debug(
                "Stream error for model: %s, message count: %d",
                self.model,
                len(messages),
            )
            raise LLMError(f"Error generating stream response: {str(e)}") from e
