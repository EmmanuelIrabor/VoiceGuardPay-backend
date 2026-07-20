from fastapi import Request
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import app


router = APIRouter()

@router.get("/webhook")
async def webhook_ping():
    return {"status": "ok"}

@router.post("/webhook")
async def webhook_receive(request: Request):
    payload = await request.json()
    print("SecurePay webhook received:", payload)
    return {"status": "received"}