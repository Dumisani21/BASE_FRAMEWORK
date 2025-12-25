"""
BASE ORM Exception Classes

Custom exception hierarchy for clear and specific error handling.
"""


class BaseORMException(Exception):
    """Base exception for all BASE ORM errors."""
    pass


class DoesNotExist(BaseORMException):
    """Raised when a query returns no results when one was expected."""
    pass


class MultipleObjectsReturned(BaseORMException):
    """Raised when a query returns multiple results when one was expected."""
    pass


class ValidationError(BaseORMException):
    """Raised when model validation fails."""
    
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.errors = errors or {}


class IntegrityError(BaseORMException):
    """Raised when database integrity constraints are violated."""
    pass


class MigrationError(BaseORMException):
    """Raised when migration operations fail."""
    pass


class ConnectionError(BaseORMException):
    """Raised when database connection fails."""
    pass


class FieldError(BaseORMException):
    """Raised when field definition or usage is invalid."""
    pass


class QueryError(BaseORMException):
    """Raised when query construction or execution fails."""
    pass
