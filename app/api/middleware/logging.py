import time

from fastapi import Request

from app import logger


async def log_requests(request: Request, call_next):
    start = time.time()
    logger.debug(f"REQUEST: {request.method} {request.url}")
    response = await call_next(request)
    duration = round(time.time() - start, 4)
    logger.debug(f"RESPONSE: {request.method} {request.url} - {response.status_code} [{duration}s]")
    return response
