
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
import os

from database.connection import supabase

router = APIRouter(prefix="/attendance", tags=["Attendance"])
security = HTTPBearer(auto_error=False)


def current_user(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
):
    try:
        payload = jwt.decode(
            credentials.credentials,
            os.environ.get("JWT_SECRET", "secret"),
            algorithms=["HS256"],
        )
        return payload
    except Exception:
        raise HTTPException(401, "Invalid or expired token")


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
):
    if not credentials:
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            os.environ.get("JWT_SECRET", "secret"),
            algorithms=["HS256"],
        )
        return payload
    except Exception:
        return None


@router.post("/in")
def attendance_in(
    user_id: Optional[str] = Query(None),
    auth_user=Depends(get_current_user_optional),
):
    effective_user_id = user_id or (auth_user.get("sub") if auth_user else None)
    if not effective_user_id:
        raise HTTPException(400, "user_id is required")

    now = datetime.now(timezone.utc)

    # Check for existing open session
    result = (
        supabase.table("user_activity")
        .select("number")
        .eq("user_id", effective_user_id)
        .eq("login", True)
        .eq("logout", False)
        .limit(1)
        .execute()
    )

    if result.data:
        return {
            "message": "Attendance session already active",
            "user_id": effective_user_id,
            "record": result.data,
        }

    saved = (
        supabase.table("user_activity")
        .insert({
            "user_id": effective_user_id,
            "login": True,
            "login_time": now.isoformat(),
            "login_date": now.date().isoformat(),
            "logout": False,
            "idle_time_minutes": 0.0,
            "activity": "PRESENT",
            "created_at": now.isoformat(),
        })
        .execute()
    )

    return {
        "message": "Attendance PRESENT",
        "user_id": effective_user_id,
        "record": saved.data,
    }


@router.post("/out")
def attendance_out(
    user_id: str = Query(...),
    idle_time_minutes: float = Query(0.0),
):
    now = datetime.now(timezone.utc)

    result = (
        supabase.table("user_activity")
        .select("number")
        .eq("user_id", user_id)
        .eq("login", True)
        .eq("logout", False)
        .order("number", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        saved = (
            supabase.table("user_activity")
            .insert({
                "user_id": user_id,
                "login": True,
                "login_time": now.isoformat(),
                "login_date": now.date().isoformat(),
                "logout": True,
                "logout_time": now.isoformat(),
                "logout_date": now.date().isoformat(),
                "idle_time_minutes": idle_time_minutes,
                "activity": "LOGOUT",
                "created_at": now.isoformat(),
            })
            .execute()
        )
        return {"message": "Attendance OUT saved", "record": saved.data}

    record_id = result.data[0]["number"]

    saved = (
        supabase.table("user_activity")
        .update({
            "logout": True,
            "logout_time": now.isoformat(),
            "logout_date": now.date().isoformat(),
            "idle_time_minutes": idle_time_minutes,
            "activity": "LOGOUT",
        })
        .eq("number", record_id)
        .execute()
    )

    return {"message": "Attendance OUT saved", "record": saved.data}
