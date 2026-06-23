import time
import uuid
import logging
from fastapi import Request

logger = logging.getLogger("api")


async def log_request(request: Request, call_next):
    request_id = str(uuid.uuid4())
    start = time.time()

    response = await call_next(request)
    latency = round((time.time() - start) * 1000, 2)

    logger.info(
        "request_complete",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "latency_ms": latency,
        },
    )
    return response
