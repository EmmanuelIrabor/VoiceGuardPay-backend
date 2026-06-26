# app/api/routes/voice.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.voice_pattern import VoicePattern
from app.services import azure_voice_service

router = APIRouter()


@router.post("/enroll")
async def enroll_voice_sample(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pattern = await db.scalar(
        select(VoicePattern).where(VoicePattern.user_id == current_user.id)
    )

    if pattern is None:
        profile_id = await azure_voice_service.create_profile()
        pattern = VoicePattern(user_id=current_user.id, azure_profile_id=profile_id)
        db.add(pattern)
        await db.commit()
        await db.refresh(pattern)

    audio_bytes = await file.read()
    result = await azure_voice_service.enroll_audio(pattern.azure_profile_id, audio_bytes)

    if result.get("enrollmentStatus") == "Enrolled":
        pattern.enrollment_status = "enrolled"
        await db.commit()

    return result


@router.post("/verify")
async def verify_voice_sample(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pattern = await db.scalar(
        select(VoicePattern).where(VoicePattern.user_id == current_user.id)
    )
    if pattern is None or pattern.enrollment_status != "enrolled":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No completed voice enrollment found for this user.",
        )

    audio_bytes = await file.read()
    result = await azure_voice_service.verify_audio(pattern.azure_profile_id, audio_bytes)
    return result