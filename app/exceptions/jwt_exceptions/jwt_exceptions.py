from app.domain.exceptions.domain_exception import DomainException


class JwtException(DomainException):
    status_code = 400
    message = "jwt operation failed"


class InvalidJwtPayloadException(JwtException):
    message = "Invalid refresh token payload"


class JwtNotFoundException(JwtException):
    status_code = 404
    message = "Refresh token not found"


class JwtRevokedException(JwtException):
    status_code = 401
    message = "Refresh token revoked"


class JwtExpiredException(JwtException):
    status_code = 401
    message = "Refresh token expired"
