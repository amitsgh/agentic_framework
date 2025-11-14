"""Custom Exception Classes"""


class FrameworkException(Exception):
    """Base exception for framework errors"""


class ConfigurationError(FrameworkException):
    """Configuration-related errors"""


class DocumentProcessingError(FrameworkException):
    """Document processing errors"""


class DatabaseError(FrameworkException):
    """Database operation errors"""


class EmbeddingError(FrameworkException):
    """Embedding generation errors"""


class LLMError(FrameworkException):
    """LLM operation errors"""


class ValidationError(FrameworkException):
    """Validation errors"""