from app.domain.exceptions.domain_exception import DomainException


class UserException(DomainException):
    status_code = 400
    message = "User operation failed"

class UsernameAlreadyExistsException(UserException):
    message = "Username already exists"

class EmailAlreadyExistsException(UserException):
    message = "Email already exists"

class UserNotFoundException(UserException):
    status_code = 404
    message = "User not found"

class LoginFailedException(UserException):
    status_code = 401
    message = "Invalid username or password"
