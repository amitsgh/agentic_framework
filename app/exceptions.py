"""Base Exception Classes"""


class FrameworkException(Exception):
    """Base exception for framework errors"""
    status_code = 500


class ConfigurationError(FrameworkException):
    """Configuration-related errors"""
    status_code = 500


class DocumentProcessingError(FrameworkException):
    """Document processing errors"""
    status_code = 422


class DatabaseError(FrameworkException):
    """Database operation errors"""
    status_code = 500


class EmbeddingError(FrameworkException):
    """Embedding generation errors"""
    status_code = 500


class LLMError(FrameworkException):
    """LLM operation errors"""
    status_code = 500


class ValidationError(FrameworkException):
    """Validation errors"""
    status_code = 400
