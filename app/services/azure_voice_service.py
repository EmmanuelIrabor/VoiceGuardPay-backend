# app/services/azure_voice_service.py
"""
Wraps Azure's Speaker Recognition REST API (text-independent verification).
Docs: https://learn.microsoft.com/azure/ai-services/speech-service/speaker-recognition-overview
"""

import httpx
from app.core.config import settings

BASE_URL = f"https://{settings.AZURE_SPEECH_REGION}.api.cognitive.microsoft.com/speaker/verification/v2.0"

HEADERS = {
    "Ocp-Apim-Subscription-Key": settings.AZURE_SPEECH_KEY,
    "Content-Type": "application/json",
}


async def create_profile() -> str:
    """Creates a new (empty) voice profile on Azure. Returns the profileId."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/text-independent/profiles",
            headers=HEADERS,
            json={"locale": "en-us"},  # locale affects activation phrase language, not verification
        )
        response.raise_for_status()
        return response.json()["profileId"]


async def enroll_audio(profile_id: str, audio_bytes: bytes) -> dict:
    """Submits one audio sample toward enrollment. Azure needs 20s+ total across calls."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/text-independent/profiles/{profile_id}/enrollments",
            headers={**HEADERS, "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000"},
            content=audio_bytes,
        )
        response.raise_for_status()
        return response.json()  # contains enrollmentStatus: "Enrolling" or "Enrolled"


async def verify_audio(profile_id: str, audio_bytes: bytes) -> dict:
    """Compares a new audio sample against the enrolled profile."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/text-independent/profiles/{profile_id}/verify",
            headers={**HEADERS, "Content-Type": "audio/wav; codecs=audio/pcm; samplerate=16000"},
            content=audio_bytes,
        )
        response.raise_for_status()
        return response.json()  # contains recognitionResult: "Accept" or "Reject", and score