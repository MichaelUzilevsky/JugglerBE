class DomainException(Exception):
    """Base class for all domain-level exceptions."""
    status_code: int = 500
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None):
        if message:
            self.message = message
        super().__init__(self.message)
