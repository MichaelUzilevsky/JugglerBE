from fastapi import Request
from fastapi.responses import JSONResponse

from app import logger
from app.domain.exceptions.domain_exception import DomainException


async def domain_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    if isinstance(exc, DomainException):
        logger.error(exc.message, exc_info=True, extra={
            "event": "domain_exception",
            "path": str(request.url)
        })
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message}
        )
    # fallback for other exceptions
    logger.critical(str(exc), exc_info=True, extra={"event": "unhandled_exception", "path": str(request.url)})
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error"}
    )


# Optional: fallback for unhandled exceptions
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.critical(str(exc), exc_info=True, extra={"event": "unhandled_exception", "path": str(request.url)})
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
