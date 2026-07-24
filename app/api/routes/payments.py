from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.securepayapi import initiate_payment

router = APIRouter(prefix="/payments")


class InitiatePaymentRequest(BaseModel):
    recipient_name: str
    account_number: str
    amount: float
    narration: str = ""


@router.post("")
def create_payment(payload: InitiatePaymentRequest):
    try:
        result = initiate_payment(
            recipient_name=payload.recipient_name,
            account_number=payload.account_number,
            amount=payload.amount,
            narration=payload.narration,
        )
        return result
    except NotImplementedError:
        raise HTTPException(status_code=501, detail="SecurePay transfer method not yet wired")