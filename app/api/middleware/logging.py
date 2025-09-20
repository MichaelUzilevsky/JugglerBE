import time
import uuid

from fastapi import Request
from starlette.responses import Response

from app import logger
from app.api.middleware.context import request_id_ctx


async def log_requests(request: Request, call_next):
    # assign a unique request_id
    request_id = str(uuid.uuid4())
    request_id_ctx.set(request_id)

    start_time = time.time()
    client_host = request.client.host if request.client else "unknown"

    # --- log request start ---
    logger.info(
        f"{request.method} {request.url.path} from {client_host}",
        extra={"request_id": request_id, "client": client_host},
    )

    try:
        response: Response = await call_next(request)
        duration = round(time.time() - start_time, 4)

        # --- log request end ---
        logger.info(
            f"{request.method} {request.url.path} {response.status_code} ({duration}s)",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duration_s": duration,
            },
        )
        return response

    except Exception as e:
        duration = round(time.time() - start_time, 4)

        # --- log error ---
        logger.error(
            f"✖ {request.method} {request.url.path} failed after {duration}s: {e}",
            extra={"request_id": request_id, "error": str(e)},
            exc_info=True,
        )
        raise
