
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from routers.attendance import current_user
from database.connection import supabase

router = APIRouter(prefix="/monitoring", tags=["Monitoring"])


class MonitoringEvent(BaseModel):
    
    user_id: str
    activity: str
    idle_reason: str | None = None
    idle_minutes: float | None = None
    application_name: str | None = None


@router.post("/event")
def save_event(
    event: MonitoringEvent,
):
    user_id = event.user_id

    result = (
        supabase.table("users_activity")
        .select("number,idle_time_minutes")
        .eq("user_id", user_id)
        .eq("login", True)
        .eq("logout", False)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise HTTPException(409, "Login before monitoring")

    row = result.data[0]
    now = datetime.now(timezone.utc)

    update = {
        "activity": event.activity,
        "user_id":user_id,
    }

    if event.idle_reason is not None:
        update["idle_reason"] = event.idle_reason

    if event.application_name is not None:
        update["application_name"] = event.application_name

    if event.idle_minutes is not None:
        previous = float(row.get("idle_time_minutes") or 0)
        update["idle_time_minutes"] = previous + max(
            0, event.idle_minutes
        )

    saved = (
        supabase.table("users_activity")
        .update(update)
        .eq("number", row["number"])
        .execute()
    )

    return {"message": "Monitoring event saved", "record": saved.data}
