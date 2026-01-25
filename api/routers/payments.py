
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from api.services.stripe_service import stripe_service

from api.services.auth_service import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])

class CheckoutRequest(BaseModel):
    plan: str # 'pro' or 'elite'

@router.post("/create-checkout")
async def create_checkout(req: CheckoutRequest, user_id: str = Depends(get_current_user)):
    return await stripe_service.create_checkout_session(user_id, req.plan)

@router.get("/status")
def get_subscription_status(user_id: str = Depends(get_current_user)):
    return stripe_service.get_user_subscription(user_id)

from fastapi import Request, Header

@router.post("/webhook")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None)):
    payload = await request.body()
    return await stripe_service.handle_webhook(payload, stripe_signature)
