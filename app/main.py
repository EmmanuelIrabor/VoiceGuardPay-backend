from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import auth
from app.api.routes import voice

app = FastAPI(title="VoiceGuardPay API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(voice.router, prefix="/voice", tags=["voice"])

@app.get("/health")
def health():
    return {"status": "ok"}


@app.options("/{rest_of_path:path}")
async def options_route(rest_of_path: str):
    return {}