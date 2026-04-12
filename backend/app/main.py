import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware

from app.routers import convert, emoji, emoji_stream, wizard
from app.routers.wizard import start_cleanup_task


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_cleanup_task()
    yield


limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="PetMoji API", version="0.1.0", docs_url=None, redoc_url=None, lifespan=lifespan
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'"
        )
        if os.getenv("ENVIRONMENT") == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요."},
    )


ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Session-Token"],
)

app.include_router(emoji.router, prefix="/api")
app.include_router(emoji_stream.router, prefix="/api")
app.include_router(convert.router, prefix="/api")
app.include_router(wizard.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
