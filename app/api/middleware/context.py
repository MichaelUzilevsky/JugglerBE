# context variable to store request_id per async task
import contextvars

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id")
