import logging

from app.api.middleware.context import request_id_ctx


class ContextFilter(logging.Filter):
    """Inject request_id and other contextvars into logs."""

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            record.request_id = request_id_ctx.get()
        except LookupError:
            record.request_id = "-"
        return True
