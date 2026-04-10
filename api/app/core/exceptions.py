"""
Custom domain exceptions for the Forex Predictor API.

Why a hierarchy: Services raise these framework-agnostic exceptions;
the global handlers in main.py translate them to HTTP responses.
This keeps the service layer decoupled from FastAPI.
"""


class BaseAppException(Exception):
    """Base class for all custom application exceptions."""

    def __init__(self, message: str = "An unexpected application error occurred.") -> None:
        self.message = message
        super().__init__(self.message)


class ModelNotLoadedError(BaseAppException):
    """Raised when an ML model artifact fails to load or is missing."""

    def __init__(self, message: str = "The ML model could not be loaded.") -> None:
        super().__init__(message)


class DataFetchError(BaseAppException):
    """Raised when historical data cannot be retrieved from the source."""

    def __init__(self, message: str = "Failed to fetch historical data.") -> None:
        super().__init__(message)


class DataValidationError(BaseAppException):
    """Raised when incoming data fails domain-level validation rules."""

    def __init__(self, message: str = "The provided data failed validation.") -> None:
        super().__init__(message)


class InsufficientDataError(BaseAppException):
    """
    Raised when there is not enough data to perform an operation.

    Why separate from DataValidationError: This signals a quantity
    issue (e.g. need 24 rows but received 10), not a format issue.
    """

    def __init__(self, message: str = "Insufficient data to perform the requested operation.") -> None:
        super().__init__(message)
