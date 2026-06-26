"""
App configuration. Reads from environment variables.

Locally: put these in a `.env` file at the project root (see .env.example).
On Vercel: set these under Project Settings -> Environment Variables.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Neon Postgres ────────────────────────────────────────────────
    # Use the POOLED connection string from Neon (has "-pooler" in the hostname).
    # Neon dashboard -> your project -> Connection Details -> Pooled connection.
    # Format: postgresql+asyncpg://<user>:<password>@<host>/<dbname>?sslmode=require
    APP_DATABASE_URL: str = ""  # <-- PASTE NEON POOLED CONNECTION STRING HERE (.env)

    # Direct (non-pooled) URL — only needed for running Alembic migrations.
    # Neon dashboard -> Connection Details -> Direct connection.
    DATABASE_URL_DIRECT: str = ""  # <-- PASTE NEON DIRECT CONNECTION STRING HERE (.env)

    # ── Auth / JWT ───────────────────────────────────────────────────
    # Generate one with: python -c "import secrets; print(secrets.token_urlsafe(32))"
    JWT_SECRET_KEY: str = ""  # <-- PASTE GENERATED SECRET HERE (.env)
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24h, demo-friendly

    # ── CORS ─────────────────────────────────────────────────────────
    # Your deployed Next.js frontend URL + localhost for dev.
    FRONTEND_ORIGIN: str = "https://voice-guard-pay.vercel.app"  # <-- UPDATE with your Vercel frontend URL

    AZURE_SPEECH_KEY: str = ""
    AZURE_SPEECH_REGION: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
