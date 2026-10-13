"""Typed errors shared across layers; the API maps each one to an HTTP status."""


class AppError(Exception):
    """Base class for expected, user-reportable errors."""


class VectorStoreUnavailable(AppError):
    pass


class RerankerUnavailable(AppError):
    pass


class LLMError(AppError):
    pass


class LLMUnavailable(LLMError):
    pass


class LLMTimeout(LLMError):
    pass


class RateLimited(AppError):
    pass
