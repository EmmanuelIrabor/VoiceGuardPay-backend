"""
FastAPI app instance. This is what both `uvicorn` (local) and Vercel's
Python runtime (prod, via api/index.py) ultimately serve.
"""

import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import auth
from app.api.routes import voice


app = FastAPI(title="VoiceGuardPay API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def debug_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "type": type(exc).__name__,
            "trace": traceback.format_exc(),
        },
    )


app.include_router(auth.router, prefix="/auth", tags=["auth"])


app.include_router(voice.router, prefix="/voice", tags=["voice"])


@app.get("/health")
def health():
    return {"status": "ok"}


"""
FastAPI app instance. This is what both `uvicorn` (local) and Vercel's
Python runtime (prod, via api/index.py) ultimately serve.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth
from app.api.routes import voice
from app.core.config import settings

app = FastAPI(title="VoiceGuardPay API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "https://voice-guard-pay.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])


@app.get("/health")
def health():
    return {"status": "ok"}