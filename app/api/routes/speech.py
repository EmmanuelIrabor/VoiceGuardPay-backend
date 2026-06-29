# app/api/routes/speech.py — new route
from fastapi.responses import Response
from app.services.azure_voice_service import text_to_speech
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User

router = APIRouter()


@router.post("/speak")
async def speak(payload: dict, current_user=Depends(get_current_user)):
    audio_bytes = await text_to_speech(payload["text"])
    return Response(content=audio_bytes, media_type="audio/mpeg")