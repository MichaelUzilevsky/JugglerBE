from app.domain.exceptions.domain_exception import DomainException


class TeamException(DomainException):
    status_code = 400
    message = "Team operation failed"


class TeamNotFoundException(TeamException):
    status_code = 404
    message = "Team not found"


class TeamAlreadyExistsException(TeamException):
    message = "Team with this name already exists"


class TeamPermissionDeniedException(TeamException):
    status_code = 403
    message = "Your team does not have permission for this order purpose"


class TeamPermissionAlreadyExistsException(TeamException):
    message = "This permission already exists for the team"


class TeamPermissionNotFoundException(TeamException):
    status_code = 404
    message = "This permission does not exist for the team"
