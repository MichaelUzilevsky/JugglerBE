from app.domain.exceptions.domain_exception import DomainException


class OrderException(DomainException):
    status_code = 400
    message = "Order operation failed"


class OrderConflictException(OrderException):
    status_code = 409
    message = "Order conflict occurred"


class OrderValidationException(OrderException):
    status_code = 422
    message = "Order validation failed"


class OrderNotFoundException(OrderException):
    status_code = 404
    message = "Order not found"
