from app.domain.exceptions.domain_exception import DomainException


class ResourceException(DomainException):
    status_code = 400
    message = "Resource operation failed"


class ResourceAlreadyExistsException(ResourceException):
    message = "Resource already exists"


class ResourceNotFoundException(ResourceException):
    status_code = 404
    message = "Resource not found"

