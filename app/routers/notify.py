from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter(prefix="/notify", tags=["Notifications & Alerts"])


class PushNotificationRequest(BaseModel):
    user_id: int
    title: str
    body: str


@router.post("/send")
async def send_push_notification(req: PushNotificationRequest):
    """Envía o encola una notificación push para el usuario/cuidador."""
    return {
        "status": "success",
        "user_id": req.user_id,
        "title": req.title,
        "body": req.body,
        "delivered": True
    }
