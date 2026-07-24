# app/api/routes/voice_command.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.intent_service import classify_utterance

router = APIRouter()


class UtteranceInput(BaseModel):
    text: str


@router.post("/classify")
async def classify(
    payload: UtteranceInput,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await classify_utterance(payload.text)

    if not result.get("is_transactional"):
        return {"status": "ignored"}

    recipient_name = result.get("recipient")
    amount = result.get("amount")

    if not recipient_name or not amount:
        return {
            "status": "needs_clarification",
            "message": "I didn't catch the amount or recipient clearly. Could you repeat that?",
        }

    matches = await db.scalars(
        select(User)
        .where(User.name.ilike(f"%{recipient_name}%"))
        .where(User.id != current_user.id)
    )
    matches = matches.all()

    if len(matches) == 0:
        return {
            "status": "needs_clarification",
            "message": f"I couldn't find anyone named {recipient_name}. Could you confirm the name?",
        }

    if len(matches) > 1:
        return {
            "status": "needs_disambiguation",
            "message": f"I found {len(matches)} people matching '{recipient_name}'. Which one?",
            "candidates": [{"id": str(u.id), "name": u.name} for u in matches],
            "amount": amount,
        }

  
    return {
        "status": "ready",
        "recipient_id": str(matches[0].id),
        "recipient_name": matches[0].name,
        "amount": amount,
    }