from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import uuid, logging, time, sys, asyncio

from app.models.log import RequestLogData
from app.utils.utils import get_client_ip

def default_log_handler(log_data: RequestLogData):
    logger = logging.getLogger("request_logger")
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        logger.propagate = False
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('%(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    level_int = logging.getLevelNamesMapping()[log_data.level]
    logger.log(level_int, log_data.model_dump_json())

class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, log_handler: Callable[[RequestLogData], None] | None = None,
                 exclude_paths: set[str] | None = None):
        super().__init__(app)
        self.log_handler = log_handler or default_log_handler
        self.exclude_paths = exclude_paths if exclude_paths is not None else {"/health"}
        
        
    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        start_time = time.perf_counter_ns()
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        response = None
        status_code = 500
        exception = None
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as e:
            exception = repr(e)
            raise
        finally:
            process_time = round((time.perf_counter_ns()-start_time)/1000000, 2)
            client_ip = get_client_ip(request)
            if response is not None:
                response.headers["Process-Time-ms"] = str(process_time)
                response.headers["X-Request-ID"] = request_id
            log_data = RequestLogData(
                level="ERROR" if exception else "INFO",
                timestamp=datetime.now(timezone.utc),
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=status_code,
                process_time_ms=process_time,
                client_ip=client_ip,
                user_agent=request.headers.get("user-agent", None),
                exception=exception
            )
            try:
                await asyncio.to_thread(self.log_handler, log_data)
            except Exception:
                logging.getLogger("request_logger").exception("log handler failed")