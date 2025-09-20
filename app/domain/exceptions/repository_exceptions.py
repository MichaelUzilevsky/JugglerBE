from app.domain.exceptions.domain_exception import DomainException


class RepositoryException(DomainException):
    status_code = 500
    message = "Database error"

class IntegrityViolationException(RepositoryException):
    status_code = 400
    message = "Integrity constraint violated"

class NotFoundException(RepositoryException):
    status_code = 404
    message = "Resource not found"
