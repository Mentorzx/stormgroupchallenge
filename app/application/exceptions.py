class ApplicationError(Exception):
    """Base class for application-level errors."""


class ValidationError(ApplicationError):
    def __init__(self, message: str, *, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


class NotFoundError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ExternalServiceError(ApplicationError):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
