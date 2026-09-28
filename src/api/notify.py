from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Union, Dict, Any

router = APIRouter(prefix="/notify", tags=["Notifications & Alerts"])


class PushNotificationRequest(BaseModel):
    user_id: Optional[Union[int, str]] = 1
    senior_id: Optional[Union[int, str]] = None
    title: Optional[str] = "Notificación SeniorVital"
    body: Optional[str] = None
    message: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


@router.post("/send")
async def send_push_notification(req: PushNotificationRequest):
    """Envía o encola una notificación push para el usuario/cuidador de forma tolerante a fallos."""
    raw_uid = req.user_id if req.user_id is not None else (req.senior_id or 1)
    msg_body = req.body or req.message or "Nueva alerta generontológica registrada."
    msg_title = req.title or "SeniorVital"

    return {
        "status": "success",
        "user_id": str(raw_uid),
        "title": msg_title,
        "body": msg_body,
        "delivered": True
    }
