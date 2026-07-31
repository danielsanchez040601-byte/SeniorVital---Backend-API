import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from contextlib import asynccontextmanager

from seniorvital_shared import get_pool, init_pool, close_pool

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "")
VAPID_CLAIM_EMAIL = os.getenv("VAPID_CLAIM_EMAIL", "admin@seniorvital.com")

VAPID_KEYS = {
    "public_key": VAPID_PUBLIC_KEY,
    "private_key": VAPID_PRIVATE_KEY,
}


class SubscribeRequest(BaseModel):
    user_id: str
    subscription: dict


class SendNotificationRequest(BaseModel):
    user_id: str
    title: str
    body: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_pool(owner="notify")
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS push_subscriptions (
                user_id TEXT PRIMARY KEY,
                endpoint TEXT NOT NULL,
                p256dh TEXT NOT NULL,
                auth TEXT NOT NULL
            )
        """)
    yield
    await close_pool(owner="notify")


app = FastAPI(
    title="Notification Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
)


@app.post("/notify/subscribe")
async def subscribe(req: SubscribeRequest):
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO push_subscriptions (user_id, endpoint, p256dh, auth)
               VALUES ($1, $2, $3, $4)
               ON CONFLICT (user_id) DO UPDATE
               SET endpoint = $2, p256dh = $3, auth = $4""",
            req.user_id,
            req.subscription.get("endpoint", ""),
            req.subscription.get("keys", {}).get("p256dh", ""),
            req.subscription.get("keys", {}).get("auth", ""),
        )
    return {"detail": "Subscribed"}


async def send_push_notification(user_id: str, title: str, body: str):
    try:
        from pywebpush import webpush, WebPushException

        pool = await get_pool()
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM push_subscriptions WHERE user_id = $1", user_id
            )
            if not row:
                return

        sub_info = {
            "endpoint": row["endpoint"],
            "keys": {"p256dh": row["p256dh"], "auth": row["auth"]},
        }
        message = json.dumps({"title": title, "body": body})

        try:
            webpush(
                subscription_info=sub_info,
                data=message,
                vapid_private_key=VAPID_KEYS["private_key"],
                vapid_claims={"sub": f"mailto:{VAPID_CLAIM_EMAIL}"},
            )
        except WebPushException as ex:
            if ex.response and ex.response.status_code == 410:
                async with pool.acquire() as conn:
                    await conn.execute(
                        "DELETE FROM push_subscriptions WHERE user_id = $1", user_id
                    )
    except ImportError:
        pass


@app.post("/notify/send")
async def send_notification(req: SendNotificationRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(send_push_notification, req.user_id, req.title, req.body)
    return {"detail": "Notification queued"}
