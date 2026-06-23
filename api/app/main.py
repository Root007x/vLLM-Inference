from fastapi import FastAPI, Depends, Request
from fastapi.responses import StreamingResponse

from .schemas import ChatRequest
from .auth import auth
from .llm import generate, stream, check_concurrency
from .limiter import limiter

from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .logging_config import setup_logging
from .middleware import log_request

setup_logging()

app = FastAPI(
    title="LLM Inference API",
)

app.middleware("http")(log_request)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

Instrumentator().instrument(app).expose(app)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/chat")
@limiter.limit("10000/minute")
async def chat(request: Request, body: ChatRequest, authorized: bool = Depends(auth)):
    return await generate(body)


@app.post("/v1/chat/stream")
@limiter.limit("10000/minute")
async def chat_stream(
    request: Request, body: ChatRequest, authorized: bool = Depends(auth)
):
    check_concurrency()
    return StreamingResponse(stream(body), media_type="text/event-stream")
