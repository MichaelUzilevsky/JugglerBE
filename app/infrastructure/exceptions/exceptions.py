class RepositoryException(Exception):
    """Generic repository error"""


class IntegrityViolationException(RepositoryException):
    """Raised when a DB constraint (unique, FK, etc.) is violated"""


class NotFoundException(RepositoryException):
    """Raised when an entity is not found in the DB"""
